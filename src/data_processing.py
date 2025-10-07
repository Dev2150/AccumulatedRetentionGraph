import json
import math

from aqt import mw

from .constants import CAT_LEARNING, INTERVAL_LEARNING_MAX, INTERVAL_YOUNG_MAX, CAT_YOUNG, INTERVAL_MATURE_MAX, \
	CAT_MATURE, CAT_RETAINED, COLOR_RETAINED, COLOR_MATURE, COLOR_YOUNG, COLOR_LEARNING, COLOR_RETENTION_ABSOLUTE, \
	COLOR_RETENTION_RELATIVE, COLOR_STABILITY_AVERAGE
from .translations import tr


def get_card_category(revlog_type, last_interval_days):
	if revlog_type in (0, 2, 3):  # Learn, Relearn, Cram
		return CAT_LEARNING
	if revlog_type == 1:  # Review
		if last_interval_days <= INTERVAL_LEARNING_MAX:
			return CAT_LEARNING
		elif last_interval_days <= INTERVAL_YOUNG_MAX:
			return CAT_YOUNG
		elif last_interval_days <= INTERVAL_MATURE_MAX:
			return CAT_MATURE
		else:
			return CAT_RETAINED
	return CAT_LEARNING  # Default


def fsrs_retrievability(elapsed_days, stability):
	"""
	Calcula a retrievability.
	Para este gráfico, usamos a fórmula do FSRS-4.5 que é mais robusta
	quando a estabilidade (S) é apenas uma aproximação (usando o ivl).
	A fórmula do FSRS-6 é muito sensível e produz valores irrealistas sem a S real.
	"""
	if stability <= 0:
		return 0.0

	# Fórmula FSRS-4.5: R(t) = (1 + t / (9 * S)) ^ -1
	return math.pow(1.0 + elapsed_days / (9.0 * stability), -1.0)


def get_card_evolution_data(self_instance, graph_id="evolutionGraph"):
	period_days = self_instance._periodDays()

	try:
		day_cutoff_s = self_instance.col.sched.day_cutoff
	except AttributeError:
		day_cutoff_s = self_instance.col.sched.dayCutoff

	# Verificar se é tela principal (CompleteCollectionStats) e aplicar configuração
	is_main_screen = hasattr(self_instance, '_deck_id')  # Nossa classe customizada tem este atributo

	# Para tela de estatísticas, usar o chunk sugerido pelo Anki
	# Para tela principal, usar configuração do addon
	if is_main_screen:
		# Lógica para tela principal (mantém a configuração do addon)
		config = mw.addonManager.getConfig(__name__)
		aggregation_config = config.get("main_screen_aggregation")

		if aggregation_config == "d":
			aggregation_chunk_days = 1
		else:  # 'w' ou default
			aggregation_chunk_days = 7
	else:
		# Para tela de estatísticas, usar o chunk sugerido pelo Anki
		try:
			raw_chunk_from_anki = self_instance.get_start_end_chunk()
			if raw_chunk_from_anki and len(raw_chunk_from_anki) > 2:
				aggregation_chunk_days = raw_chunk_from_anki[2]
			else:
				# Fallback baseado no tipo se get_start_end_chunk falhar
				stats_type_from_instance = getattr(self_instance, 'type', 3)
				if stats_type_from_instance == 0:  # 1 Mês
					aggregation_chunk_days = 1
				elif stats_type_from_instance == 1:  # 3 Meses
					aggregation_chunk_days = 7
				elif stats_type_from_instance == 2:  # 1 Ano
					aggregation_chunk_days = 30
				else:  # Deck Life (All)
					aggregation_chunk_days = 30
		except (IndexError, AttributeError, TypeError):
			# Fallback se qualquer erro ocorrer
			stats_type_from_instance = getattr(self_instance, 'type', 3)
			if stats_type_from_instance == 0:
				aggregation_chunk_days = 1
			elif stats_type_from_instance == 1:
				aggregation_chunk_days = 7
			else:
				aggregation_chunk_days = 30

	unit_suffix = "d"
	if aggregation_chunk_days == 7:
		unit_suffix = "w"
	elif aggregation_chunk_days >= 28:  # Inclui 30 e outros próximos para "mês"
		unit_suffix = "m"

	end_date_timestamp_ms = day_cutoff_s * 1000
	graph_start_day_idx = 0

	revlog_deck_tag_filter_sql = self_instance._revlogLimit()

	if period_days is not None and period_days > 0:
		graph_start_day_idx = -(period_days - 1)
	else:  # Deck life ou period_days é 0 ou None
		first_rev_query_conditions = []
		if revlog_deck_tag_filter_sql:
			first_rev_query_conditions.append(revlog_deck_tag_filter_sql)
		first_rev_query = "SELECT MIN(id) FROM revlog"
		if first_rev_query_conditions:
			first_rev_query += " WHERE " + " AND ".join(first_rev_query_conditions)
		min_revlog_id_ms = self_instance.col.db.scalar(first_rev_query)
		if not min_revlog_id_ms:  # Se não há revisões, retorna dados vazios
			return [], {}, "", aggregation_chunk_days
		days_ago = (day_cutoff_s - (min_revlog_id_ms / 1000)) // 86400
		graph_start_day_idx = -int(days_ago)

	main_revlog_query_conditions = ["id < " + str(end_date_timestamp_ms)]
	if revlog_deck_tag_filter_sql:
		main_revlog_query_conditions.append(revlog_deck_tag_filter_sql)

	config = mw.addonManager.getConfig(__name__)
	exclude_deleted = config.get("exclude_deleted_cards")  # Padrão True se não encontrado
	exclude_suspended = config.get("exclude_suspended_cards")  # Padrão False se não encontrado

	if exclude_deleted:
		main_revlog_query_conditions.append("cid IN (SELECT id FROM cards)")

	if exclude_suspended:
		main_revlog_query_conditions.append("cid IN (SELECT id FROM cards WHERE queue != -1)")

	query = """
        SELECT id, cid, type, ivl
        FROM revlog
        WHERE """ + " AND ".join(main_revlog_query_conditions) + """
        ORDER BY id ASC
    """
	all_reviews = self_instance.col.db.all(query)

	if not all_reviews:
		return [], {}, "", aggregation_chunk_days

	card_current_states = {}
	daily_graph_data_points = {}
	daily_etk_points = {}
	daily_etk_percent_points = {}
	daily_stability_points = {}

	current_rev_idx = 0
	for day_offset in range(graph_start_day_idx, 1):  # Itera dia a dia
		current_day_end_ts_ms = (day_cutoff_s + (day_offset * 86400)) * 1000
		if day_offset == 0:  # Hoje
			current_day_end_ts_ms = end_date_timestamp_ms

		processed_reviews_on_this_day_iteration = False
		while current_rev_idx < len(all_reviews):
			rev_id_ms, cid, rev_type, rev_ivl = all_reviews[current_rev_idx]
			if rev_id_ms < current_day_end_ts_ms:
				cat = get_card_category(rev_type, rev_ivl)
				card_current_states[cid] = {
					'category': cat,
					'ivl': rev_ivl,
					'last_rev_time': rev_id_ms
				}
				current_rev_idx += 1
				processed_reviews_on_this_day_iteration = True
			else:
				break

		daily_graph_data_points[day_offset] = {
			CAT_LEARNING: 0, CAT_YOUNG: 0, CAT_MATURE: 0, CAT_RETAINED: 0
		}

		# Laço unificado para cálculo
		total_retrievability_for_day = 0
		active_cards_for_etk = 0
		total_stability_for_day = 0
		day_counts_recalc = {CAT_LEARNING: 0, CAT_YOUNG: 0, CAT_MATURE: 0, CAT_RETAINED: 0}

		for cid, state in card_current_states.items():
			if state['last_rev_time'] < current_day_end_ts_ms:
				active_cards_for_etk += 1
				day_counts_recalc[state['category']] += 1

				last_rev_day_s = state['last_rev_time'] / 1000
				last_rev_day_idx = int((last_rev_day_s - day_cutoff_s) / 86400)

				days_since_review = day_offset - last_rev_day_idx
				if days_since_review < 0:
					continue

				stability = max(state['ivl'], 0.1)  # Usar ivl como aproximação de estabilidade, evitar divisão por zero
				total_stability_for_day += stability

				# Fórmula de Retrievability FSRS
				retrievability = fsrs_retrievability(days_since_review, stability)
				total_retrievability_for_day += retrievability

		day_counts = day_counts_recalc

		daily_etk_points[day_offset] = total_retrievability_for_day
		if active_cards_for_etk > 0:
			daily_etk_percent_points[day_offset] = (total_retrievability_for_day / active_cards_for_etk) * 100
		else:
			daily_etk_percent_points[day_offset] = 0

		if day_offset > graph_start_day_idx and not processed_reviews_on_this_day_iteration:
			if (day_offset - 1) in daily_graph_data_points:
				daily_graph_data_points[day_offset] = daily_graph_data_points[day_offset - 1].copy()
		else:
			daily_graph_data_points[day_offset] = day_counts

		if active_cards_for_etk > 0:
			daily_stability_points[day_offset] = total_stability_for_day / active_cards_for_etk
		else:
			daily_stability_points[day_offset] = 0

	# Certificar que o dia 0 (hoje) tem os dados corretos finais
	final_day_counts = {CAT_LEARNING: 0, CAT_YOUNG: 0, CAT_MATURE: 0, CAT_RETAINED: 0}
	for card_id, state in card_current_states.items():
		if state['last_rev_time'] < end_date_timestamp_ms:
			final_day_counts[state['category']] += 1
	daily_graph_data_points[0] = final_day_counts

	# Agregar dados diários em chunks (semanas, meses)
	aggregated_flot_data = {CAT_LEARNING: {}, CAT_YOUNG: {}, CAT_MATURE: {}, CAT_RETAINED: {}}
	aggregated_etk_data = {}
	aggregated_etk_absolute_data = {}
	aggregated_etk_percent_data = {}
	aggregated_avg_stability_data = {}
	etk_absolute_temp_accumulator = {}
	etk_percent_temp_accumulator = {}
	avg_stability_temp_accumulator = {}

	for day_idx in sorted(daily_graph_data_points.keys()):
		x_flot_chunk_idx = -math.floor(-day_idx / aggregation_chunk_days)

		aggregated_flot_data[CAT_LEARNING][x_flot_chunk_idx] = daily_graph_data_points[day_idx][CAT_LEARNING]
		aggregated_flot_data[CAT_YOUNG][x_flot_chunk_idx] = daily_graph_data_points[day_idx][CAT_YOUNG]
		aggregated_flot_data[CAT_MATURE][x_flot_chunk_idx] = daily_graph_data_points[day_idx][CAT_MATURE]
		aggregated_flot_data[CAT_RETAINED][x_flot_chunk_idx] = daily_graph_data_points[day_idx][CAT_RETAINED]

		aggregated_etk_data[x_flot_chunk_idx] = daily_etk_points.get(day_idx, 0)

		if x_flot_chunk_idx not in etk_absolute_temp_accumulator:
			etk_absolute_temp_accumulator[x_flot_chunk_idx] = []
		etk_absolute_temp_accumulator[x_flot_chunk_idx].append(daily_etk_points.get(day_idx, 0))

		if x_flot_chunk_idx not in etk_percent_temp_accumulator:
			etk_percent_temp_accumulator[x_flot_chunk_idx] = []
		etk_percent_temp_accumulator[x_flot_chunk_idx].append(daily_etk_percent_points.get(day_idx, 0))

		if x_flot_chunk_idx not in avg_stability_temp_accumulator:
			avg_stability_temp_accumulator[x_flot_chunk_idx] = []
		avg_stability_temp_accumulator[x_flot_chunk_idx].append(daily_stability_points.get(day_idx, 0))

	for chunk_idx, values in etk_absolute_temp_accumulator.items():
		aggregated_etk_absolute_data[chunk_idx] = daily_etk_points.get(chunk_idx, 0)

	for chunk_idx, values in etk_percent_temp_accumulator.items():
		aggregated_etk_percent_data[chunk_idx] = sum(values) / len(values) if values else 0

	for chunk_idx, values in avg_stability_temp_accumulator.items():
		aggregated_avg_stability_data[chunk_idx] = sum(values) / len(values) if values else 0

	series = []
	data_learning, data_young, data_mature, data_retained, data_etk_absolute, data_etk_percent, data_avg_stability  = [], [], [], [], [], [], []

	all_x_flot_chunk_indices = sorted(list(set(aggregated_etk_data.keys())))

	if not all_x_flot_chunk_indices and graph_start_day_idx == 0:
		all_x_flot_chunk_indices.append(0)

	for x_chunk_idx in all_x_flot_chunk_indices:
		data_learning.append([x_chunk_idx, aggregated_flot_data[CAT_LEARNING].get(x_chunk_idx, 0)])
		data_young.append([x_chunk_idx, aggregated_flot_data[CAT_YOUNG].get(x_chunk_idx, 0)])
		data_mature.append([x_chunk_idx, aggregated_flot_data[CAT_MATURE].get(x_chunk_idx, 0)])
		data_retained.append([x_chunk_idx, aggregated_flot_data[CAT_RETAINED].get(x_chunk_idx, 0)])
		data_etk_absolute.append([x_chunk_idx, aggregated_etk_absolute_data.get(x_chunk_idx, 0)])
		data_etk_percent.append([x_chunk_idx, aggregated_etk_percent_data.get(x_chunk_idx, 0)])
		data_avg_stability.append([x_chunk_idx, aggregated_avg_stability_data.get(x_chunk_idx, 0)])


	config = mw.addonManager.getConfig(__name__)

	if not config.get("hide_retained"):
		series.append(
			{"data": data_retained, "label": tr("label_retained"), "color": COLOR_RETAINED, "bars": {"order": 1}})
	if not config.get("hide_mature"):
		series.append({"data": data_mature, "label": tr("label_mature"), "color": COLOR_MATURE, "bars": {"order": 2}})
	if not config.get("hide_young"):
		series.append({"data": data_young, "label": tr("label_young"), "color": COLOR_YOUNG, "bars": {"order": 3}})
	if not config.get("hide_learning"):
		series.append(
			{"data": data_learning, "label": tr("label_learning"), "color": COLOR_LEARNING, "bars": {"order": 4}})

	if not config.get("hide_total_knowledge_graph"):
		series.append({
			"data": data_etk_absolute,
			"label": tr("label_total_knowledge"),
			"color": COLOR_RETENTION_ABSOLUTE,
			"lines": {"show": True, "lineWidth": 2, "fill": False},
			"bars": {"show": False},
			"stack": False,
			"yaxis": 1
		})

	y2label = ""
	is_showing_y2 = False
	y2_max = None
	if not config.get("secondary_axis_dynamic_max"):
		y2_max = config.get("secondary_axis_maximum_value")


	secondary_graph = config.get("secondary_graph")
	if secondary_graph == 'retention_relative':
		series.append({
			"data": data_etk_percent,
			"label": tr("label_avg_retention_percent"),
			"color": COLOR_RETENTION_RELATIVE,
			"lines": {"show": True, "lineWidth": 2, "fill": False},
			"bars": {"show": False},
			"stack": False,
			"yaxis": 2
		})
		y2label = tr("graph_y_label_stability_days")
	elif secondary_graph == 'stability_average':
		series.append({
			"data": data_avg_stability,
			"label": tr("label_avg_stability"),
			"color": COLOR_STABILITY_AVERAGE,
			"lines": {"show": True, "lineWidth": 2, "fill": False},
			"bars": {"show": False},
			"stack": False,
			"yaxis": 2
		})
		y2label = tr("graph_y_label_percent")
		is_showing_y2 = True

	min_x_val_for_axis = 0
	max_x_val_for_axis = 0
	if all_x_flot_chunk_indices:
		min_x_val_for_axis = all_x_flot_chunk_indices[0]
		max_x_val_for_axis = all_x_flot_chunk_indices[-1]
		if max_x_val_for_axis < 0:
			max_x_val_for_axis = 0
		elif not (0 in all_x_flot_chunk_indices):
			max_x_val_for_axis = 0

	xaxis_min = min_x_val_for_axis - 0.5
	xaxis_max = max_x_val_for_axis + 0.5

	tr_today = tr("label_today")
	use_absolute_dates = config.get("use_absolute_dates")

	month_translations = []
	for i in range(1, 13):
		month_key = ["month_jan", "month_feb", "month_mar", "month_apr", "month_may", "month_jun",
					 "month_jul", "month_aug", "month_sep", "month_oct", "month_nov", "month_dec"][i - 1]
		month_translations.append(tr(month_key))

	months_js_array = '["' + '", "'.join(month_translations) + '"]'

	if use_absolute_dates:
		tick_formatter_js = f"""
function(val, axis) {{
    if (Math.abs(val - 0) < 0.0001) {{ return '{tr_today}'; }}
    var date = new Date(({day_cutoff_s} + (val * {aggregation_chunk_days} * 86400)) * 1000);
    var months = {months_js_array};
    return months[date.getMonth()] + ' ' + date.getDate();
}}
"""
	else:
		tick_formatter_js = f"""
function(val, axis) {{
    var suffix = '{unit_suffix}';
    if (Math.abs(val - 0) < 0.0001) {{ return '{tr_today}'; }}
    return val.toFixed(axis.options.tickDecimals === undefined ? 0 : axis.options.tickDecimals) + suffix;
}}
"""

	etk_percent_data_json = json.dumps(aggregated_etk_percent_data)
	etk_abs_data_json = json.dumps(aggregated_etk_data)
	stability_avg_data_json = json.dumps(aggregated_avg_stability_data)

	tooltip_html = f"""
<script>
$(function() {{
    var etkAbsData = {etk_abs_data_json};
    var etkStabData = {stability_avg_data_json};
    var tooltip = $("#evolutionGraphTooltip");
    if (!tooltip.length) {{
        tooltip = $('<div id="evolutionGraphTooltip" style="position:absolute;display:none;padding:8px;background-color:#fff;border:1px solid #ddd;color:#333;border-radius:4px;box-shadow:0 2px 5px rgba(0,0,0,0.1);pointer-events:none;font-size:0.9em;z-index:100;"></div>').appendTo("body");
    }}
    $("#{graph_id}").bind("plothover", function (event, pos, item) {{
        if (item) {{
            var x_val_on_axis = item.datapoint[0];
            var totalForDay = 0;
            var etkAbsValue = "N/A";
            var etkPercentValue = "N/A";
            var etkAvgValue = "N/A";

            var plot = $(this).data("plot");
            var allSeries = plot.getData();
            var pointData = {{}};

            for(var i=0; i < allSeries.length; ++i){{
                 var currentSeries = allSeries[i];
                 if (!currentSeries.label) continue;
                for(var j=0; j < currentSeries.data.length; ++j){{
                    var d = currentSeries.data[j];
                    if(Math.abs(d[0] - x_val_on_axis) < 0.0001){{
                         if(!pointData[x_val_on_axis]) pointData[x_val_on_axis] = {{}};
                         pointData[x_val_on_axis][currentSeries.label] = d[1];
                     }}
                }}
            }}

            var today_str = '{tr_today}';
            var titleX = item.series.xaxis.tickFormatter(x_val_on_axis, item.series.xaxis);

            var content = "<b>{tr("tooltip_period")}" + titleX + "</b><br/>";
            var labelLearning = "{tr("label_learning")}";
            var labelYoung = "{tr("label_young")}";
            var labelMature = "{tr("label_mature")}";
            var labelRetained = "{tr("label_retained")}";
            var labelRetentionPercent = "{tr("label_avg_retention_percent")}";

            if(pointData[x_val_on_axis]){{
                if(pointData[x_val_on_axis][labelLearning] !== undefined) totalForDay += pointData[x_val_on_axis][labelLearning];
                if(pointData[x_val_on_axis][labelYoung] !== undefined) totalForDay += pointData[x_val_on_axis][labelYoung];
                if(pointData[x_val_on_axis][labelMature] !== undefined) totalForDay += pointData[x_val_on_axis][labelMature];
                if(pointData[x_val_on_axis][labelRetained] !== undefined) totalForDay += pointData[x_val_on_axis][labelRetained];
                
                if(etkAbsData[x_val_on_axis] !== undefined) {{
                    etkAbsValue = etkAbsData[x_val_on_axis].toFixed(0);
                    etkPercentValue = (100 * etkAbsData[x_val_on_axis] / totalForDay).toFixed(1)
                }}
                if(etkStabData[x_val_on_axis] !== undefined) {{
                    etkAvgValue = etkStabData[x_val_on_axis].toFixed(0);
                }}
            }}
            
            content += labelLearning + ": " + (pointData[x_val_on_axis]?.[labelLearning]?.toFixed(0) || 0) + "<br/>";
            content += labelYoung + ": " + (pointData[x_val_on_axis]?.[labelYoung]?.toFixed(0) || 0) + "<br/>";
            content += labelMature + ": " + (pointData[x_val_on_axis]?.[labelMature]?.toFixed(0) || 0) + "<br/>";
            content += labelRetained + ": " + (pointData[x_val_on_axis]?.[labelRetained]?.toFixed(0) || 0) + "<br/>";
            content += "<i>{tr("tooltip_total")}" + totalForDay.toFixed(0) + "</i><br/><hr style='margin: 4px 0; border-top: 1px solid #ccc;'/>";
            content += "<b>" + labelRetentionPercent + ": " + etkPercentValue + "</b><br/>";
            content += "<b>{tr("label_total_knowledge")}: " + etkAbsValue + "</b><br/>";
            content += "<b>{tr("label_avg_stability")}: " + etkAvgValue + "</b>";

            tooltip.html(content).css({{top: item.pageY+5, left: item.pageX+5}}).fadeIn(200);
        }} else {{
            tooltip.hide();
        }}
    }});
}});
</script>
"""
	graph_options = {
		"xaxis": {
			"min": xaxis_min,
			"max": xaxis_max,
			"tickFormatter": tick_formatter_js,
		},
		"yaxes": [
			{"min": 0, "position": "left"},
			{"min": 0, "max": y2_max, "position": "right", "alignTicksWithAxis": 1, "show": is_showing_y2}
		],
		"series": {
			"stack": True,
			"bars": {
				"show": True,
				"align": "center",
				"barWidth": 0.9,
				"lineWidth": 1,
				"fill": 0.8
			}
		},
		"grid": {"hoverable": True, "clickable": True, "borderColor": "#C0C0C0"},
		"legend": {
			"show": True,
			"position": "nw",
			"backgroundColor": "#ffffff",
			"backgroundOpacity": 0
		}
	}
	return series, graph_options, tooltip_html, aggregation_chunk_days, y2label
