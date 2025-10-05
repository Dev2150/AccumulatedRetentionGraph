import json
import re
import time

from anki.utils import ids2str
from aqt import mw
from aqt.deckbrowser import DeckBrowser, DeckBrowserContent
# Imports adicionais
from aqt.gui_hooks import overview_will_render_content, deck_browser_will_render_content
from aqt.overview import Overview, OverviewContent

from .rendering import render_card_evolution_graph
from .translations import tr


# Classe Helper para gerar estatísticas da tela principal.
# Movida para fora das funções de hook para evitar re-declaração.
class CompleteCollectionStats:
	"""Helper class to generate main screen statistics.
	Moved outside the hook functions to avoid redeclaration."""

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
			# Para períodos customizados, escolhe tipo baseado na duração
			period_days = self._periodDays()
			if period_days is None:  # deck_life
				self.type = 3
			elif period_days <= 30:  # até 1 mês
				self.type = 0
			elif period_days <= 90:  # até 3 meses
				self.type = 1
			elif period_days <= 365:  # até 1 ano
				self.type = 2
			else:  # mais de 1 ano
				self.type = 3

	def _periodDays(self):
		if self._period == "1m":
			return 30
		elif self._period == "3m":
			return 90
		elif self._period == "1y":
			return 365
		elif self._period == "deck_life":
			return None
		else:
			# Tenta interpretar como Xm (X meses) ou Xy (X anos)
			match = re.match(r'^(\d+)([my])$', self._period)
			if match:
				number, unit = int(match.group(1)), match.group(2)
				if unit == 'm':  # meses
					return number * 30
				elif unit == 'y':  # anos
					return number * 365
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

		aggregation_config = config.get("main_screen_aggregation")

		if aggregation_config == "d":
			chunk_days = 1
		else:
			chunk_days = 7

		# Usa _periodDays() para calcular o período em dias
		period_days = self._periodDays()

		if period_days is not None:
			return (day_cutoff_s - (period_days * 86400), day_cutoff_s, chunk_days)
		else:  # deck_life
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
		html_parts.append('<h3 style="text-align: center; margin-bottom: 0; color: #333;">')
		html_parts.append(safe_title)
		html_parts.append('</h3>')
		if safe_subtitle:
			html_parts.append(
				'<p style="text-align: center; color: #666; margin-top: 0.2em; margin-bottom: 0.5em; font-size: 0.9em;">')
			html_parts.append(safe_subtitle)
			html_parts.append('</p>')
		return ''.join(html_parts)

	def _graph(self, id, data, conf, ylabel="", y2label="", tooltip_html=""):
		config = mw.addonManager.getConfig(__name__)
		height = config.get("main_screen_height")
		safe_ylabel = ylabel.replace('%', '%%')
		safe_y2label = y2label.replace('%', '%%')

		# Extrai o conteúdo JS puro do tooltip_html
		tooltip_js_content = ""
		if tooltip_html:
			match = re.search(r'<script[^>]*>(.*?)</script>', tooltip_html, re.DOTALL)
			if match:
				tooltip_js_content = match.group(1).strip()
				# Remove a função de auto-execução $(function() { ... }); para que possamos chamá-la diretamente
				tooltip_js_content = re.sub(r'^\s*\$\(function\(\)\s*\{', '', tooltip_js_content)
				tooltip_js_content = re.sub(r'\}\s*\)\;\s*$', '', tooltip_js_content)

		try:
			if not data or not any(s.get('data') for s in data):
				return '<div style="color:#888;text-align:center;margin:1em 0;">' + tr("graph_no_data") + '</div>'

			data_json_for_js = json.dumps(data)
			options_json_for_js = json.dumps(conf)

			py_unit_suffix = conf.get('xaxis', {}).get('unit_suffix', 'd')
			py_agg_days = conf.get('xaxis', {}).get('aggregation_chunk_days', 1)
			py_today_label = tr("label_today").replace('%', '%%')

			# Get day_cutoff_s to pass to JS for absolute dates
			try:
				py_day_cutoff_s = self.col.sched.day_cutoff
			except AttributeError:
				py_day_cutoff_s = self.col.sched.dayCutoff  # For older Anki versions

			html_parts = []
			html_parts.append(
				'<div id="' + id + '" style="height:' + str(height) + 'px; width:95%; margin: 0 auto;"></div>')
			html_parts.append(
				'<p style="text-align: center; font-size: 0.8em; color: #666; margin-top: 0.5em;">' + safe_ylabel + '</p>')

			js_parts = ['<script type="text/javascript">', '(function() {', '  var attempts = 0;',
						'  var maxAttempts = 20;', '  var retryInterval = 200;', '  ',
						'  function checkDependencies() {',
						'    return (typeof $ !== "undefined" && typeof $.plot !== "undefined");', '  }', '  ',
						'  function loadFlotLibraries(callback) {', '    if (typeof $ === "undefined") {',
						'      console.error("Card Evolution JS: jQuery not available");', '      return false;',
						'    }', '    ', '    if (typeof $.plot === "undefined") {',
						'      var flotScript = document.createElement("script");',
						'      flotScript.src = "https://cdnjs.cloudflare.com/ajax/libs/flot/0.8.3/jquery.flot.min.js";',
						'      flotScript.onload = function() {',
						'        var stackScript = document.createElement("script");',
						'        stackScript.src = "https://cdnjs.cloudflare.com/ajax/libs/flot/0.8.3/jquery.flot.stack.min.js";',
						'        stackScript.onload = function() {', '          setTimeout(callback, 100);',
						'        };', '        stackScript.onerror = function() {',
						'          console.error("Card Evolution JS: Failed to load Flot stack plugin");',
						'          setTimeout(callback, 100);', '        };',
						'        document.head.appendChild(stackScript);', '      };',
						'      flotScript.onerror = function() {',
						'        console.error("Card Evolution JS: Failed to load Flot from CDN");',
						'        callback();', '      };', '      document.head.appendChild(flotScript);',
						'      return false;', '    }', '    ', '    callback();', '    return true;', '  }', '  ',
						'  function renderGraph() {', '    try {', '      var graphDiv = $("#' + id + '");',
						'      if (graphDiv.length === 0) {', '', '        return false;', '      }', '      ',
						'      var data = ' + data_json_for_js + ';',
						'      var options = ' + options_json_for_js + ';', '      ',
						'      if (options.xaxis && typeof options.xaxis.tickFormatter === "string") {',
						'        delete options.xaxis.tickFormatter;', '      }', '      ',
						'      if (options.series) {', '        options.series.stack = true;',
						'        if (options.series.bars) {', '          options.series.bars.show = true;',
						'        } else {', '          options.series.bars = { show: true };', '        }',
						'      } else {', '        options.series = { stack: true, bars: { show: true } };', '      }',
						'      ']

			use_absolute_dates = config.get("use_absolute_dates")

			# Criar array de meses traduzidos para JavaScript
			month_translations_main = []
			for i in range(1, 13):
				month_key = ["month_jan", "month_feb", "month_mar", "month_apr", "month_may", "month_jun",
							 "month_jul", "month_aug", "month_sep", "month_oct", "month_nov", "month_dec"][i - 1]
				month_translations_main.append(tr(month_key))
			months_js_array_main = '["' + '", "'.join(month_translations_main) + '"]'

			if use_absolute_dates:
				formatter_func_str = 'function(val, axis) { var todayLabel = \'' + py_today_label + '\'; if (Math.abs(val - 0) < 0.001) { return todayLabel; } var aggDays = ' + str(
					py_agg_days) + '; var dayCutoffS = ' + str(
					py_day_cutoff_s) + '; var dayOffset = val * aggDays; var date = new Date((dayCutoffS + (dayOffset * 86400)) * 1000); var months = ' + months_js_array_main + '; return months[date.getMonth()] + \' \' + date.getDate(); }'
			else:
				formatter_func_str = 'function(val, axis) { var unitSuffix = \'' + py_unit_suffix + '\'; var todayLabel = \'' + py_today_label + '\'; if (Math.abs(val - 0) < 0.001) { return todayLabel; } var decimals = axis.options.tickDecimals === undefined ? 0 : axis.options.tickDecimals; return val.toFixed(decimals) + unitSuffix; }'

			js_parts += ['      options.xaxis.tickFormatter = ' + formatter_func_str + ';', '      ',
						 '      $.plot(graphDiv, data, options);', '      ', '      ' + tooltip_js_content, '      ',
						 '',
						 '      return true;', '    } catch (e) {',
						 '      console.error("Card Evolution JS: Error rendering graph on attempt " + attempts + ":", e);',
						 '      return false;', '    }', '  }', '  ', '  function attemptRender() {', '    attempts++;',
						 '    ', '    if (attempts > maxAttempts) {',
						 '      console.error("Card Evolution JS: Failed to render graph after " + maxAttempts + " attempts. Dependencies or DOM may not be ready.");',
						 '      return;', '    }', '    ', '    if (!checkDependencies()) {',
						 '      loadFlotLibraries(function() {', '        setTimeout(attemptRender, retryInterval);',
						 '      });', '      return;', '    }', '    ', '    if (renderGraph()) {', '      return;',
						 '    }', '    ', '    setTimeout(attemptRender, retryInterval);', '  }', '  ',
						 '  function initWhenReady() {', '    if (document.readyState === "loading") {',
						 '      document.addEventListener("DOMContentLoaded", function() {',
						 '        setTimeout(attemptRender, 50);', '      });', '    } else {',
						 '      setTimeout(attemptRender, 50);', '    }', '  }', '  ', '  initWhenReady();', '})();',
						 '</script>']

			return ''.join(html_parts) + ''.join(js_parts)

		except Exception as e:
			import traceback
			print("Card Evolution Main Screen: Erro ao gerar HTML/JS do gráfico (Python): " + str(e))
			print("Card Evolution Main Screen: Traceback (Python): " + str(traceback.format_exc()))
			return '<div style="color:red;text-align:center;">Erro Py ao gerar gráfico: ' + str(e) + '</div>'


def _render_main_screen_graph_html(deck_id=None):
	"""Generates the complete HTML for the main screen chart.
	Gera o HTML completo para o gráfico da tela principal."""

	config = mw.addonManager.getConfig(__name__)
	period = config.get("main_screen_period")
	stats_instance = CompleteCollectionStats(mw.col, deck_id=deck_id, period=period)

	graph_html = render_card_evolution_graph(stats_instance)

	# Envolve o gráfico renderizado em um contêiner pai, agora com estilo.
	return f'<div class="evolution-graph-main-wrapper" style="max-width: 900px; margin: 20px auto; padding: 1em; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9;">{graph_html}</div>'


def on_deck_browser_render(deck_browser: DeckBrowser, content: DeckBrowserContent):
	"""Adds the status evolution graph to the deck browser main screen.
	Adiciona o gráfico de evolução do status à tela principal do navegador de baralhos."""
	config = mw.addonManager.getConfig(__name__)
	if not config.get("show_in_deck_browser"):
		return

	try:
		# Para o navegador de baralhos, não filtramos por deck_id (None)
		graph_html = _render_main_screen_graph_html(deck_id=None)
		content.stats += graph_html
	except Exception as e:
		print(f"Accumulated Retention: Failed to render graph on deck browser: {e}")


def on_overview_render(overview: Overview, content: OverviewContent):
	"""Adds the status evolution graph to the deck overview screen.
	Adiciona o gráfico de evolução do status à tela de visão geral do baralho."""
	config = mw.addonManager.getConfig(__name__)
	if not config.get("show_in_overview"):
		return

	try:
		# Para a visão geral, usamos o ID do baralho atual, obtido via mw.
		current_deck_id = mw.col.decks.get_current_id()
		graph_html = _render_main_screen_graph_html(deck_id=current_deck_id)

		# Injetar o gráfico, envolvendo-o em uma linha de tabela para renderização correta.
		content.table += f'<tr><td colspan="2" style="padding: 10px 0;">{graph_html}</td></tr>'

	except Exception as e:
		print(f"Accumulated Retention: Failed to render graph on overview: {e}")


def init_main_screen_hooks():
	"""Initializes hooks for the main screen (Deck Browser).
	Inicializa os ganchos para a tela principal (Navegador de Baralhos)."""
	config = mw.addonManager.getConfig(__name__)
	if config.get("enable_main_screen"):
		# Checking show_in_overview/deck_browser is done inside each hook.
		# A verificação de show_in_overview/deck_browser é feita dentro de cada hook.
		overview_will_render_content.append(on_overview_render)
		deck_browser_will_render_content.append(on_deck_browser_render)
