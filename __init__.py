from anki import stats
from anki.hooks import wrap
from anki.utils import ids2str
from aqt import mw
from .translations import tr # Adicionado para tradução
# import anki.pylib.text as text # This module seems to no longer exist or be needed here
import time
import math # Adicionado para math.floor
import json
import re

# Card State Categories & Colors
CAT_LEARNING = 0
CAT_YOUNG = 1
CAT_MATURE = 2
CAT_RETAINED = 3

COLOR_LEARNING = stats.colLearn
COLOR_YOUNG = stats.colYoung
COLOR_MATURE = stats.colMature
COLOR_RETAINED = "#004080" # Dark blue, adjust as needed

# Interval thresholds (in days)
INTERVAL_LEARNING_MAX = 7
INTERVAL_YOUNG_MAX = 21
INTERVAL_MATURE_MAX = 84

def get_card_category(revlog_type, last_interval_days):
    if revlog_type in (0, 2, 3): # Learn, Relearn, Cram
        return CAT_LEARNING
    if revlog_type == 1: # Review
        if last_interval_days <= INTERVAL_LEARNING_MAX:
            return CAT_LEARNING
        elif last_interval_days <= INTERVAL_YOUNG_MAX:
            return CAT_YOUNG
        elif last_interval_days <= INTERVAL_MATURE_MAX:
            return CAT_MATURE
        else:
            return CAT_RETAINED
    return CAT_LEARNING # Default

def get_card_evolution_data(self_instance, graph_id="evolutionGraph"):
    period_days = self_instance._periodDays()

    try:
        day_cutoff_s = self_instance.col.sched.day_cutoff
    except AttributeError:
        day_cutoff_s = self_instance.col.sched.dayCutoff

    # Verificar se é tela principal (CompleteCollectionStats) e aplicar configuração
    is_main_screen = hasattr(self_instance, '_deck_id')  # Nossa classe customizada tem este atributo
    
    # stats_type: 0=1m, 1=3m, 2=1y, 3=all(deck life)
    # No Anki, parece que _periodDays retorna None para "all" (type 3),
    # e type 2 (1 year) também pode se comportar como "all" em termos de _periodDays, mas tem um tipo distinto.
    # get_start_end_chunk()[2] é o chunk_days_for_aggregation sugerido pelo Anki.
    # Esperado: 1 para 1m, 7 para 3m, 30 para 1y/all.

    stats_type_from_instance = getattr(self_instance, 'type', 3) # Default para 'all' se não encontrar
    raw_chunk_from_anki = None
    anki_suggested_chunk_days = 1 # Default inicial

    try:
        raw_chunk_from_anki = self_instance.get_start_end_chunk()
        if raw_chunk_from_anki and len(raw_chunk_from_anki) > 2:
            anki_suggested_chunk_days = raw_chunk_from_anki[2]
        else:
            # Se get_start_end_chunk não retornar o esperado, recorremos ao tipo.
            if stats_type_from_instance == 0: anki_suggested_chunk_days = 1
            elif stats_type_from_instance == 1: anki_suggested_chunk_days = 7
            else: anki_suggested_chunk_days = 30 # 1y ou all

    except (IndexError, AttributeError, TypeError) as e_chunk:
        if stats_type_from_instance == 0: anki_suggested_chunk_days = 1
        elif stats_type_from_instance == 1: anki_suggested_chunk_days = 7
        else: anki_suggested_chunk_days = 30 # 1y ou all

    # Para tela principal, usar configuração; para tela de stats, usar lógica original
    if is_main_screen:
        config = mw.addonManager.getConfig(__name__)
        aggregation_config = config.get("main_screen_aggregation", "w")
        
        if aggregation_config == "d":
            aggregation_chunk_days = 1
        else:  # 'w' ou default
            aggregation_chunk_days = 7
            
    else:
        # Lógica original para tela de estatísticas
        if stats_type_from_instance == 0: # 1 Mês
            aggregation_chunk_days = 1
        elif stats_type_from_instance == 1: # 3 Meses
            aggregation_chunk_days = 7
        elif stats_type_from_instance == 2: # 1 Ano
            aggregation_chunk_days = 30 
        elif stats_type_from_instance == 3: # Deck Life (All)
            aggregation_chunk_days = 30
        else: # Fallback para segurança, embora não deva acontecer
            aggregation_chunk_days = anki_suggested_chunk_days

    unit_suffix = "d"
    if aggregation_chunk_days == 7:
        unit_suffix = "w"
    elif aggregation_chunk_days >= 28: # Inclui 30 e outros próximos para "mês"
        unit_suffix = "m"
    
    end_date_timestamp_ms = day_cutoff_s * 1000
    graph_start_day_idx = 0 
    
    revlog_deck_tag_filter_sql = self_instance._revlogLimit()

    if period_days is not None and period_days > 0:
        graph_start_day_idx = -(period_days - 1)
    else: # Deck life ou period_days é 0 ou None
        first_rev_query_conditions = []
        if revlog_deck_tag_filter_sql:
            first_rev_query_conditions.append(revlog_deck_tag_filter_sql)
        first_rev_query = "SELECT MIN(id) FROM revlog"
        if first_rev_query_conditions:
            first_rev_query += " WHERE " + " AND ".join(first_rev_query_conditions)
        min_revlog_id_ms = self_instance.col.db.scalar(first_rev_query)
        if not min_revlog_id_ms: # Se não há revisões, retorna dados vazios
            return [], {}, ""
        days_ago = (day_cutoff_s - (min_revlog_id_ms / 1000)) // 86400
        graph_start_day_idx = -int(days_ago)

    main_revlog_query_conditions = ["id < " + str(end_date_timestamp_ms)]
    if revlog_deck_tag_filter_sql:
        main_revlog_query_conditions.append(revlog_deck_tag_filter_sql)

    config = mw.addonManager.getConfig(__name__)
    exclude_deleted = config.get("exclude_deleted_cards", True) # Padrão True se não encontrado

    if exclude_deleted:
        main_revlog_query_conditions.append("cid IN (SELECT id FROM cards)")
    
    query = """
        SELECT id, cid, type, ivl
        FROM revlog
        WHERE """ + " AND ".join(main_revlog_query_conditions) + """
        ORDER BY id ASC
    """
    all_reviews = self_instance.col.db.all(query)

    if not all_reviews:
        return [], {}, ""

    card_current_states = {}
    daily_graph_data_points = {} # Mapeia day_idx para contagens diárias

    for i in range(graph_start_day_idx, 1):
        daily_graph_data_points[i] = {
            CAT_LEARNING: 0, CAT_YOUNG: 0, CAT_MATURE: 0, CAT_RETAINED: 0
        }

    current_rev_idx = 0
    for day_offset in range(graph_start_day_idx, 1): # Itera dia a dia
        current_day_end_ts_ms = (day_cutoff_s + (day_offset * 86400)) * 1000
        if day_offset == 0: # Hoje
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
        
        day_counts = {CAT_LEARNING: 0, CAT_YOUNG: 0, CAT_MATURE: 0, CAT_RETAINED: 0}
        active_cards_today = 0
        for card_id, state in card_current_states.items():
            # Considerar apenas cartões cuja última revisão foi *antes do final* do dia atual
            # E que foram tocados em algum momento (para evitar contagem de cartões nunca vistos no período)
            if state['last_rev_time'] < current_day_end_ts_ms:
                 day_counts[state['category']] += 1
                 active_cards_today +=1
        
        if day_offset > graph_start_day_idx and not processed_reviews_on_this_day_iteration and active_cards_today == 0 :
             if (day_offset -1) in daily_graph_data_points: # Se não houve atividade e o dia anterior existe
                daily_graph_data_points[day_offset] = daily_graph_data_points[day_offset-1].copy()
        else:
            daily_graph_data_points[day_offset] = day_counts
            
    # Certificar que o dia 0 (hoje) tem os dados corretos finais
    final_day_counts = {CAT_LEARNING: 0, CAT_YOUNG: 0, CAT_MATURE: 0, CAT_RETAINED: 0}
    for card_id, state in card_current_states.items():
        if state['last_rev_time'] < end_date_timestamp_ms: # Usar o timestamp final do período
            final_day_counts[state['category']] += 1
    daily_graph_data_points[0] = final_day_counts

    # Agregar dados diários em chunks (semanas, meses)
    aggregated_flot_data = {CAT_LEARNING: {}, CAT_YOUNG: {}, CAT_MATURE: {}, CAT_RETAINED: {}}
    # As chaves dos dicionários internos serão o x_flot_chunk_idx (ex: -12, -11, ..., 0)
    
    sorted_day_indices = sorted(daily_graph_data_points.keys()) # de graph_start_day_idx a 0

    for day_idx in sorted_day_indices:
        x_flot_chunk_idx = -math.floor(-day_idx / aggregation_chunk_days)
        current_day_counts = daily_graph_data_points[day_idx]
        
        # A contagem para este chunk_idx é a do último dia encontrado para ele
        aggregated_flot_data[CAT_LEARNING][x_flot_chunk_idx] = current_day_counts[CAT_LEARNING]
        aggregated_flot_data[CAT_YOUNG][x_flot_chunk_idx] = current_day_counts[CAT_YOUNG]
        aggregated_flot_data[CAT_MATURE][x_flot_chunk_idx] = current_day_counts[CAT_MATURE]
        aggregated_flot_data[CAT_RETAINED][x_flot_chunk_idx] = current_day_counts[CAT_RETAINED]

    series = []
    data_learning, data_young, data_mature, data_retained = [], [], [], []
    
    all_x_flot_chunk_indices = sorted(list(set(
        list(aggregated_flot_data[CAT_LEARNING].keys()) +
        list(aggregated_flot_data[CAT_YOUNG].keys()) +
        list(aggregated_flot_data[CAT_MATURE].keys()) +
        list(aggregated_flot_data[CAT_RETAINED].keys())
    )))

    if not all_x_flot_chunk_indices and graph_start_day_idx == 0 : # Nenhum dado e período é apenas "hoje"
         # Adiciona um ponto em x=0 para que o gráfico não quebre se não houver revisões
         all_x_flot_chunk_indices.append(0)


    for x_chunk_idx in all_x_flot_chunk_indices:
        data_learning.append([x_chunk_idx, aggregated_flot_data[CAT_LEARNING].get(x_chunk_idx, 0)])
        data_young.append([x_chunk_idx, aggregated_flot_data[CAT_YOUNG].get(x_chunk_idx, 0)])
        data_mature.append([x_chunk_idx, aggregated_flot_data[CAT_MATURE].get(x_chunk_idx, 0)])
        data_retained.append([x_chunk_idx, aggregated_flot_data[CAT_RETAINED].get(x_chunk_idx, 0)])

    config = mw.addonManager.getConfig(__name__)
    
    # Código para adicionar séries - "stack: True" removido de cada série individual.
    # O empilhamento será controlado globalmente via JS (options.series.stack = true).
    # "bars: {"order": X}" mantido para a ordem visual dentro do empilhamento.
    if not config.get("hide_retained"):
        series.append({"data": data_retained, "label": tr("label_retained"), "color": COLOR_RETAINED, "bars": {"order": 1}})
    if not config.get("hide_mature"):
        series.append({"data": data_mature, "label": tr("label_mature"), "color": COLOR_MATURE, "bars": {"order": 2}})
    if not config.get("hide_young"):
        series.append({"data": data_young, "label": tr("label_young"), "color": COLOR_YOUNG, "bars": {"order": 3}})
    if not config.get("hide_learning"):
        series.append({"data": data_learning, "label": tr("label_learning"), "color": COLOR_LEARNING, "bars": {"order": 4}})
    
    min_x_val_for_axis = 0
    max_x_val_for_axis = 0
    if all_x_flot_chunk_indices:
        min_x_val_for_axis = all_x_flot_chunk_indices[0]
        max_x_val_for_axis = all_x_flot_chunk_indices[-1]
        # Se o último chunk não é 0 (ex: deck life onde a última revisão foi há muito tempo)
        # ou se o único chunk é negativo.
        if max_x_val_for_axis < 0 :
             max_x_val_for_axis = 0 # Garante que o eixo vá até "Hoje" visualmente se necessário
        elif not (0 in all_x_flot_chunk_indices) and max_x_val_for_axis > 0: # Caso estranho, mas para segurança
             pass # Não precisa ajustar max_x_val_for_axis
        elif not (0 in all_x_flot_chunk_indices) and min_x_val_for_axis == 0 and max_x_val_for_axis == 0 and daily_graph_data_points[0][CAT_LEARNING] == 0 and daily_graph_data_points[0][CAT_YOUNG] == 0 and daily_graph_data_points[0][CAT_MATURE] == 0 and daily_graph_data_points[0][CAT_RETAINED] == 0:
             # Caso de nenhum dado e período de apenas 1 dia (Hoje)
             pass # min_x_val_for_axis e max_x_val_for_axis já são 0.
        else: # Caso normal, onde 0 (Hoje) deve ser o limite superior ou estar incluído
             max_x_val_for_axis = 0


    xaxis_min = min_x_val_for_axis - 0.5
    xaxis_max = max_x_val_for_axis + 0.5
    
    # Construir o tickFormatter dinamicamente - SEM F-STRING
    tr_today = tr("label_today")
    tick_formatter_js = (
        "function(val, axis) {\n" +
        "    var suffix = '" + unit_suffix + "';\n" +
        "    var aggChunkDays = " + str(aggregation_chunk_days) + ";\n" +
        "    if (aggChunkDays === 1 && Math.abs(val - 0) < 0.0001) {\n" +
        "        return '" + tr_today + "';\n" +
        "    }\n" +
        "    return val.toFixed(axis.options.tickDecimals === undefined ? 0 : axis.options.tickDecimals) + suffix;\n" +
        "}"
    )

    # Passar as strings traduzidas para o JS do tooltip
    tr_tooltip_period = tr("tooltip_period")
    tr_tooltip_total = tr("tooltip_total")
    # As labels das séries já são traduzidas ao serem passadas para o Flot
    # Portanto, podemos usá-las diretamente no tooltip via item.series.label

    tooltip_html = f"""
<script>
$(function() {{
    var tooltip = $("#evolutionGraphTooltip");
    if (!tooltip.length) {{
        tooltip = $('<div id="evolutionGraphTooltip" style="position:absolute;display:none;padding:5px;border:1px solid #333;background-color:#f5f5f5;opacity:0.9;color:#000;"></div>').appendTo("body");
    }}
    $("#{graph_id}").bind("plothover", function (event, pos, item) {{
        if (item) {{
            var x_val_on_axis = item.datapoint[0];
            var y_val = item.datapoint[1];
            var seriesLabel = item.series.label; // Já traduzido
            var totalForDay = 0;

            var plot = $(this).data("plot");
            var allSeries = plot.getData();
            var pointData = {{}}; // Usar chaves de série já traduzidas

            for(var i=0; i < allSeries.length; ++i){{
                 var currentSeries = allSeries[i];
                 if (!currentSeries.label) continue;
                for(var j=0; j < currentSeries.data.length; ++j){{
                    var d = currentSeries.data[j];
                    if(Math.abs(d[0] - x_val_on_axis) < 0.0001){{
                         if(!pointData[x_val_on_axis]) pointData[x_val_on_axis] = {{}};
                         pointData[x_val_on_axis][currentSeries.label] = d[1]; // Usa a label da série como chave
                         totalForDay += d[1];
                    }}
                }}
            }}

            var xaxes_options = plot.getOptions().xaxes[0];
            var unitSuffixFromOptions = xaxes_options.unit_suffix || 'd';
            var aggregationChunkDaysFromOptions = xaxes_options.aggregation_chunk_days || 1;
            var tickDecimalsFromOptions = xaxes_options.tickDecimals === undefined ? 0 : xaxes_options.tickDecimals;
            var displayX = x_val_on_axis.toFixed(tickDecimalsFromOptions);
            var titleX;
            var today_str = '{tr_today}'; // Passa a string "Hoje" traduzida

            if (aggregationChunkDaysFromOptions === 1 && Math.abs(x_val_on_axis - 0) < 0.0001) {{
                titleX = today_str;
            }} else {{
                titleX = displayX + unitSuffixFromOptions;
            }}

            var content = "<b>{tr_tooltip_period}" + titleX + "</b><br/>";
            var labelLearning = "{tr("label_learning")}";
            var labelYoung = "{tr("label_young")}";
            var labelMature = "{tr("label_mature")}";
            var labelRetained = "{tr("label_retained")}";

            if(pointData[x_val_on_axis]){{
                // Acessar usando as labels traduzidas que foram usadas para criar as séries
                if(pointData[x_val_on_axis][labelLearning] !== undefined) content += labelLearning + ": " + pointData[x_val_on_axis][labelLearning].toFixed(0) + "<br/>";
                if(pointData[x_val_on_axis][labelYoung] !== undefined) content += labelYoung + ": " + pointData[x_val_on_axis][labelYoung].toFixed(0) + "<br/>";
                if(pointData[x_val_on_axis][labelMature] !== undefined) content += labelMature + ": " + pointData[x_val_on_axis][labelMature].toFixed(0) + "<br/>";
                if(pointData[x_val_on_axis][labelRetained] !== undefined) content += labelRetained + ": " + pointData[x_val_on_axis][labelRetained].toFixed(0) + "<br/>";
            }}
            content += "<i>{tr_tooltip_total}" + totalForDay.toFixed(0) + "</i>";

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
            "unit_suffix": unit_suffix,
            "aggregation_chunk_days": aggregation_chunk_days,
            "tickDecimals": 0 
        },
        "yaxis": {"min": 0},
        "series": {
            "stack": True,
            "bars": {
                "show": True, 
                "align": "center", 
                "barWidth": 0.9, # Largura de barra mais constante agora que os X são chunks
                "lineWidth": 1, 
                "fill": 0.8
            }
        },
        "grid": {"hoverable": True, "clickable": True, "borderColor": "#C0C0C0"},
        "legend": {"show": True, "position": "nw"}
    }
    return series, graph_options, tooltip_html

def render_card_evolution_graph(self_instance):
    graph_id = "evolutionGraph" + str(time.time()).replace('.', '')
    title = tr("graph_title")
    subtitle = tr("graph_subtitle")
    series_data, options, tooltip_html = get_card_evolution_data(self_instance, graph_id)

    # Remover prints de depuração
    if not series_data or not any(s['data'] for s in series_data):
        return "<div style='text-align:center;margin-top:1em;'>" + tr("graph_no_data") + "</div>"

    # Extrair aggregation_chunk_days das opções para usar no xunit (não mais usado para xunit, mas pode ser útil para logs ou futuras refs)
    current_aggregation_chunk_days = options.get("xaxis", {}).get("aggregation_chunk_days", 1)

    # Usar o método _title da instância para um estilo de título padrão do Anki.
    # O método _title geralmente lida com a tradução se as strings forem chaves de tradução.
    # Nossas strings title e subtitle são literais em português.
    html = self_instance._title(title, subtitle)
    html += self_instance._graph(
        id=graph_id,
        data=series_data,
        conf=options, # options contém nosso tickFormatter detalhado
        ylabel=tr("graph_y_label")
        # Nenhum parâmetro xunit aqui
    )
    html += tooltip_html
    return html

# --- Nova seção de Hooking --- 

# Tentar usar cardGraph (sem underscore)
TARGET_METHOD_NAME = "cardGraph"
BACKUP_ATTR_NAME = "_cardGraph_original_by_evolution_addon" # Manter nome do backup para consistência

# Guardar uma referência ao método original, se ainda não foi guardada por este addon
if hasattr(stats.CollectionStats, TARGET_METHOD_NAME) and not hasattr(stats.CollectionStats, BACKUP_ATTR_NAME):
    setattr(stats.CollectionStats, BACKUP_ATTR_NAME, getattr(stats.CollectionStats, TARGET_METHOD_NAME))
elif not hasattr(stats.CollectionStats, TARGET_METHOD_NAME):
    pass

def add_evolution_graph_to_card_stats(self_instance, *original_args, **original_kwargs):
    """
    Wraps the original cardGraph method to append the evolution graph.
    This version assumes the wrapper is called with only (self, *args, **kwargs) by the hook system,
    and the original method is retrieved from our backup.
    
    `self_instance` is the CollectionStats instance.
    `original_args` and `original_kwargs` are arguments for the original method (likely none for cardGraph).
    """
    original_card_graph_html = ""
    
    original_method_ref = getattr(stats.CollectionStats, BACKUP_ATTR_NAME, None)

    if original_method_ref:
        # Clean up kwargs for the original cardGraph call
        # cardGraph() typically only takes self.
        # Another addon seems to be injecting '_old' into the kwargs.
        cleaned_kwargs = original_kwargs.copy()
        if '_old' in cleaned_kwargs:
            del cleaned_kwargs['_old']
        
        # The original cardGraph() method does not accept *args or **kwargs beyond self.
        # So, we should call it with only self_instance if original_args and cleaned_kwargs are empty.
        # However, to be safe and pass through what was given (minus _old):
        try:
            original_card_graph_html = original_method_ref(self_instance, *original_args, **cleaned_kwargs)
        except TypeError as e:
            # This might happen if original_args is not empty or cleaned_kwargs still has unexpected items.
            try:
                original_card_graph_html = original_method_ref(self_instance)
            except Exception as e2:
                original_card_graph_html = "<!-- Original graph failed to load -->"

    else:
        original_card_graph_html = "<!-- Original graph could not be determined -->"
    
    evolution_graph_html = render_card_evolution_graph(self_instance)
    
    config = mw.addonManager.getConfig(__name__)
    show_at_beginning = config.get("show_at_beginning") # False por padrão (mostrar ao final)

    if show_at_beginning:
        # Mostrar o gráfico de evolução ANTES do gráfico original
        return evolution_graph_html + original_card_graph_html
    else:
        # Mostrar o gráfico de evolução DEPOIS do gráfico original (comportamento padrão)
        return original_card_graph_html + evolution_graph_html

# Aplicar o wrap apenas se o método original e o backup existirem
if hasattr(stats.CollectionStats, TARGET_METHOD_NAME) and hasattr(stats.CollectionStats, BACKUP_ATTR_NAME):
    current_target_method_func = getattr(stats.CollectionStats, TARGET_METHOD_NAME)
    original_backup_func = getattr(stats.CollectionStats, BACKUP_ATTR_NAME)

    # Desfazer o wrap se o método alvo não for já o original (ou seja, se já foi envolvido por nós)
    if current_target_method_func != original_backup_func:
        setattr(stats.CollectionStats, TARGET_METHOD_NAME, original_backup_func)

    # Aplicar o wrap
    setattr(stats.CollectionStats, TARGET_METHOD_NAME, wrap(
        original_backup_func, # Envolver o original que guardamos
        add_evolution_graph_to_card_stats, 
        "around"
    ))
else:
    if hasattr(stats.CollectionStats, TARGET_METHOD_NAME):
        pass

# Manter o print final se o carregamento foi tentado, mesmo que o hook falhe
# para dar alguma indicação de que o addon foi processado.
if not (hasattr(stats.CollectionStats, TARGET_METHOD_NAME) and hasattr(stats.CollectionStats, BACKUP_ATTR_NAME)):
     pass

# ===== INÍCIO DA INTEGRAÇÃO COM TELA PRINCIPAL =====

# Imports adicionais
from aqt.gui_hooks import overview_will_render_content, deck_browser_will_render_content
from aqt.overview import Overview, OverviewContent
from aqt.deckbrowser import DeckBrowser, DeckBrowserContent

# Classe Helper para gerar estatísticas da tela principal.
# Movida para fora das funções de hook para evitar re-declaração.
class CompleteCollectionStats:
    def __init__(self, col, deck_id=None, period="3m"):
        self.col = col
        self._deck_id = deck_id
        self._period = period
        
        if period == "1m":
            self.type = 0
        elif period == "3m":
            self.type = 1
        elif period == "1y":
            self.type = 2
        else:
            self.type = 3
            
    def _periodDays(self):
        if self._period == "1m":
            return 30
        elif self._period == "3m":
            return 90
        elif self._period == "1y":
            return 365
        else:
            return None
            
    def _revlogLimit(self):
        if not self._deck_id:
            return ""
        
        try:
            child_decks = [self._deck_id]
            for name, did in self.col.decks.children(self._deck_id):
                child_decks.append(did)
            deck_ids_str = ids2str(child_decks)
            return "cid IN (SELECT id FROM cards WHERE did IN " + deck_ids_str + ")"
        except Exception as e:
            return ""
            
    def get_start_end_chunk(self):
        config = mw.addonManager.getConfig(__name__)
        try:
            day_cutoff_s = self.col.sched.day_cutoff
        except AttributeError:
            day_cutoff_s = int(time.time())
        
        aggregation_config = config.get("main_screen_aggregation", "w")
        
        if aggregation_config == "d":
            chunk_days = 1
        else:
            chunk_days = 7
        
        if self._period == "1m":
            return (day_cutoff_s - (30 * 86400), day_cutoff_s, chunk_days)
        elif self._period == "3m":
            return (day_cutoff_s - (90 * 86400), day_cutoff_s, chunk_days)
        elif self._period == "1y":
            return (day_cutoff_s - (365 * 86400), day_cutoff_s, chunk_days)
        else:
            first_rev_query = "SELECT MIN(id) FROM revlog"
            if self._deck_id:
                try:
                    child_decks = [self._deck_id]
                    for name, did in self.col.decks.children(self._deck_id):
                        child_decks.append(did)
                    deck_ids_str = ids2str(child_decks)
                    first_rev_query += " WHERE cid IN (SELECT id FROM cards WHERE did IN " + deck_ids_str + ")"
                except:
                    pass
            
            min_revlog_id_ms = self.col.db.scalar(first_rev_query)
            if min_revlog_id_ms:
                start = min_revlog_id_ms // 1000
            else:
                start = day_cutoff_s - (365 * 86400)
            
            return (start, day_cutoff_s, chunk_days)
    
    def _title(self, title, subtitle=""):
        safe_title = title.replace('%', '%%')
        safe_subtitle = subtitle.replace('%', '%%')

        html_parts = []
        html_parts.append('<h3 style="text-align: center; margin-bottom: 0.5em; color: #333;">')
        html_parts.append(safe_title)
        html_parts.append('</h3>')
        if safe_subtitle:
            html_parts.append('<p style="text-align: center; color: #666; margin-bottom: 1em; font-size: 0.9em;">')
            html_parts.append(safe_subtitle)
            html_parts.append('</p>')
        return ''.join(html_parts)
        
    def _graph(self, id, data, conf, ylabel=""):
        config = mw.addonManager.getConfig(__name__)
        height = config.get("main_screen_height", 250)
        safe_ylabel = ylabel.replace('%', '%%')
        
        try:
            if not data or not any(s.get('data') for s in data):
                return '<div style="color:#888;text-align:center;margin:1em 0;">Sem dados para mostrar</div>'
            
            data_json_for_js = json.dumps(data)
            options_json_for_js = json.dumps(conf)

            py_unit_suffix = conf.get('xaxis', {}).get('unit_suffix', 'd')
            py_agg_days = conf.get('xaxis', {}).get('aggregation_chunk_days', 1)
            py_today_label = tr("label_today").replace('%', '%%')
            
            html_parts = []
            html_parts.append('<div id="' + id + '" style="height:' + str(height) + 'px; width:95%; margin: 0 auto;"></div>')
            html_parts.append('<p style="text-align: center; font-size: 0.8em; color: #666; margin-top: 0.5em;">' + safe_ylabel + '</p>')
            
            js_parts = []
            js_parts.append('<script type="text/javascript">')
            js_parts.append('(function() {')
            js_parts.append('  function initPlot() {')
            js_parts.append('    if (typeof $ === "undefined") { return false; }')
            js_parts.append('    if (typeof $.plot === "undefined") {')
            js_parts.append('      var flotScript = document.createElement("script");')
            js_parts.append('      flotScript.src = "https://cdnjs.cloudflare.com/ajax/libs/flot/0.8.3/jquery.flot.min.js";')
            js_parts.append('      flotScript.onload = function() {')
            js_parts.append('        var stackScript = document.createElement("script");')
            js_parts.append('        stackScript.src = "https://cdnjs.cloudflare.com/ajax/libs/flot/0.8.3/jquery.flot.stack.min.js";')
            js_parts.append('        stackScript.onload = function() { setTimeout(function() { initPlot(); }, 100); };')
            js_parts.append('        stackScript.onerror = function() { setTimeout(function() { initPlot(); }, 100); };')
            js_parts.append('        document.head.appendChild(stackScript);')
            js_parts.append('      };')
            js_parts.append('      flotScript.onerror = function() { console.error("Card Evolution JS: Failed to load Flot from CDN"); };')
            js_parts.append('      document.head.appendChild(flotScript);')
            js_parts.append('      return false;')
            js_parts.append('    }')
            js_parts.append('    $(function() {')
            js_parts.append('      setTimeout(function() {')
            js_parts.append('        try {')
            js_parts.append('          var graphDiv = $("#' + id + '");')
            js_parts.append('          if (graphDiv.length === 0) { return; }')
            js_parts.append('          var data = ' + data_json_for_js + ';')
            js_parts.append('          var options = ' + options_json_for_js + ';')
            js_parts.append('          if (options.xaxis && typeof options.xaxis.tickFormatter === "string") { delete options.xaxis.tickFormatter; }')
            js_parts.append('          if (options.series) { options.series.stack = true; if (options.series.bars) { options.series.bars.show = true; } else { options.series.bars = { show: true }; } } else { options.series = { stack: true, bars: { show: true } }; }')
            js_parts.append('          options.xaxis.tickFormatter = function(val, axis) { var unitSuffix = \'' + py_unit_suffix + '\'; var aggDays = ' + str(py_agg_days) + '; var todayLabel = \'' + py_today_label + '\'; if (aggDays === 1 && Math.abs(val - 0) < 0.001) { return todayLabel; } var decimals = axis.options.tickDecimals === undefined ? 0 : axis.options.tickDecimals; return val.toFixed(decimals) + unitSuffix; };')
            js_parts.append('          $.plot(graphDiv, data, options);')
            js_parts.append('        } catch (e) { console.error("Card Evolution Main Screen Plot JS Error (in setTimeout):", e); }')
            js_parts.append('      }, 50);')
            js_parts.append('    });')
            js_parts.append('    return true;')
            js_parts.append('  }')
            js_parts.append('  var attempts = 0;')
            js_parts.append('  function tryInit() { attempts++; if (initPlot()) { } else if (attempts < 10) { setTimeout(tryInit, 200); } else { console.error("Card Evolution JS: Failed to initialize plot. jQuery or Flot may not be loaded."); } }')
            js_parts.append('  tryInit();')
            js_parts.append('})();')
            js_parts.append('</script>')
            
            return ''.join(html_parts) + ''.join(js_parts)
            
        except Exception as e:
            import traceback
            print("Card Evolution Main Screen: Erro ao gerar HTML/JS do gráfico (Python): " + str(e))
            print("Card Evolution Main Screen: Traceback (Python): " + str(traceback.format_exc()))
            return '<div style="color:red;text-align:center;">Erro Py ao gerar gráfico: ' + str(e) + '</div>'

def _render_main_screen_graph_html(deck_id=None):
    """Gera o HTML completo para o gráfico da tela principal."""
    config = mw.addonManager.getConfig(__name__)
    period = config.get("main_screen_period", "3m")
    stats_instance = CompleteCollectionStats(mw.col, deck_id=deck_id, period=period)
    
    graph_html = render_card_evolution_graph(stats_instance)
    
    # Envolve o gráfico renderizado em um contêiner pai.
    return f'<div class="evolution-graph-main-wrapper">{graph_html}</div>'

def on_deck_browser_render(deck_browser: DeckBrowser, content: DeckBrowserContent):
    """Adiciona o gráfico na tela de listagem de baralhos (sem filtro de deck específico)."""
    config = mw.addonManager.getConfig(__name__)
    if not config.get("enable_main_screen", False) or not config.get("show_in_deck_browser", True):
        return

    try:
        # Para a tela principal (deck browser), deck_id é None para mostrar todos os decks.
        graph_html = _render_main_screen_graph_html(deck_id=None)
        content.stats += graph_html
    except Exception as e:
        print(f"Accumulated Retention: Failed to render graph on deck browser: {e}")

def on_overview_render(overview: Overview, content: OverviewContent):
    """Adiciona o gráfico na tela de visão geral de um deck específico."""
    config = mw.addonManager.getConfig(__name__)
    if not config.get("enable_main_screen", False) or not config.get("show_in_overview", True):
        return
        
    try:
        # Na visão geral, usamos o deck_id do objeto overview.
        graph_html = _render_main_screen_graph_html(deck_id=overview.deck_id)
        content.table += graph_html
    except Exception as e:
        print(f"Accumulated Retention: Failed to render graph on overview: {e}")


def init_main_screen_hooks():
    """Inicializar hooks para injetar gráfico na tela principal."""
    config = mw.addonManager.getConfig(__name__)
    if config.get("enable_main_screen", False):
        # A verificação de show_in_overview/deck_browser é feita dentro de cada hook.
        overview_will_render_content.append(on_overview_render)
        deck_browser_will_render_content.append(on_deck_browser_render)

# Inicializar hooks da tela principal
try:
    init_main_screen_hooks()
except Exception as e:
    print(f"Card Evolution: Erro ao inicializar hooks da tela principal: {e}")

# ===== FIM DA INTEGRAÇÃO COM TELA PRINCIPAL =====
