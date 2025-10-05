import time

from .data_processing import get_card_evolution_data
from .translations import tr


# --- Nova seção de Hooking ---
def render_card_evolution_graph(self_instance):
	from .main_screen_integration import CompleteCollectionStats

	graph_id = "evolutionGraph" + str(time.time()).replace('.', '')
	title = tr("graph_title")
	subtitle = tr("graph_subtitle")
	series_data, options, tooltip_html, aggregation_chunk_days = get_card_evolution_data(self_instance, graph_id)

	# Remover prints de depuração
	if not series_data or not any(s['data'] for s in series_data):
		return "<div style='text-align:center;margin-top:1em;'>" + tr("graph_no_data") + "</div>"

	# Usar o método _title da instância para um estilo de título padrão do Anki.
	# O método _title geralmente lida com a tradução se as strings forem chaves de tradução.
	# Nossas strings title e subtitle são literais em português.
	html = self_instance._title(title, subtitle)

	# A lógica de renderização agora depende do tipo de instância de estatísticas
	if isinstance(self_instance, CompleteCollectionStats):
		# Para a tela principal, passamos o tooltip_html para ser integrado pelo método _graph customizado
		html += self_instance._graph(
			id=graph_id,
			data=series_data,
			conf=options,
			ylabel=tr("graph_y_label"),
			y2label=tr("graph_y_label_percent"),
			tooltip_html=tooltip_html
		)
	else:
		# Para a tela de estatísticas padrão, usamos o método original do Anki (sem y2label)
		html += self_instance._graph(
			id=graph_id,
			data=series_data,
			conf=options,
			xunit=aggregation_chunk_days,
			ylabel=tr("graph_y_label")
		)
		html += tooltip_html

	return html
