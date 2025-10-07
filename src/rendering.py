import time

from aqt import mw

from .data_processing import get_card_evolution_data
from .translations import tr


# --- Nova seção de Hooking ---
def render_card_evolution_graph(self_instance):
	from .main_screen_integration import CompleteCollectionStats

	graph_id = "evolutionGraph" + str(time.time()).replace('.', '')
	title = tr("graph_title")
	subtitle = tr("graph_subtitle")
	series_data, options, tooltip_html, aggregation_chunk_days, y2label = get_card_evolution_data(self_instance, graph_id)

	# Remover prints de depuração
	if not series_data or not any(s['data'] for s in series_data):
		return "<div style='text-align:center;margin-top:1em;'>" + tr("graph_no_data") + "</div>"

	# Use the instance's _title method for a standard Anki title style.
	# The _title method usually handles translation if strings are translation keys.
	# Our title and subtitle strings are literals in Portuguese.

	# Usar o método _title da instância para um estilo de título padrão do Anki.
	# O método _title geralmente lida com a tradução se as strings forem chaves de tradução.
	# Nossas strings title e subtitle são literais em português.
	html = self_instance._title(title, subtitle)

	config = mw.addonManager.getConfig(__name__)

	# Rendering logic now depends on the stats instance type
	# A lógica de renderização agora depende do tipo de instância de estatísticas

	secondary_graph = config.get("secondary_graph")
	print(f'{html = }')
	print(f'{isinstance(self_instance, CompleteCollectionStats) = }')
	print(f'{secondary_graph = }')

	if isinstance(self_instance, CompleteCollectionStats):
		# For the main screen, we pass the tooltip html to be integrated by the custom _graph method
		# Para a tela principal, passamos o tooltip_html para ser integrado pelo método _graph customizado
		html += self_instance._graph(
			id=graph_id,
			data=series_data,
			conf=options,
			ylabel=tr("graph_y_label"),
			y2label=y2label,
			tooltip_html=tooltip_html
		)
	else:
		# For the default stats screen, we use the original Anki method (without y2label)
		# Para a tela de estatísticas padrão, usamos o método original do Anki (sem y2label)
		html += self_instance._graph(
			id=graph_id,
			data=series_data,
			conf=options,
			xunit=aggregation_chunk_days,
			y2label=y2label
		)

		html += tooltip_html

	return html
