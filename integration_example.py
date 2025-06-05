# -*- coding: utf-8 -*-
"""
Exemplo de como integrar o gráfico da tela principal ao addon original.
Adicione este código ao final do seu __init__.py existente.
"""

# Importar as dependências necessárias para a tela principal
from aqt.gui_hooks import (
    overview_will_render_content,
    deck_browser_will_render_content,
)
from aqt.overview import OverviewContent
from aqt.deckbrowser import DeckBrowserContent

def inject_graph_into_main_screen(content, context):
    """
    Função para injetar o gráfico na tela principal.
    Reutiliza a lógica existente do addon.
    """
    if not mw or not mw.col:
        return

    config = mw.addonManager.getConfig(__name__)
    
    # Verificar se a funcionalidade está habilitada
    if not config.get("enable_main_screen", False):
        return
    
    # Verificar tipo de tela
    if isinstance(context, OverviewContent) and not config.get("show_in_overview", True):
        return
    elif isinstance(context, DeckBrowserContent) and not config.get("show_in_deck_browser", True):
        return

    # Determinar deck_id
    deck_id = None
    graph_id_suffix = "main"
    
    if isinstance(context, OverviewContent):
        # Pegar deck atual
        if hasattr(mw.col, 'decks') and hasattr(mw.col.decks, 'current'):
            current_deck = mw.col.decks.current()
            if current_deck:
                deck_id = current_deck['id']
                graph_id_suffix = f"deck_{deck_id}"
    elif isinstance(context, DeckBrowserContent):
        deck_id = None
        graph_id_suffix = "browser"

    # Criar uma instância mock do CollectionStats para reutilizar a lógica existente
    class MockCollectionStats:
        def __init__(self, col, deck_id=None):
            self.col = col
            self._deck_id = deck_id
            self.type = 1  # 3m por padrão
            
        def _periodDays(self):
            # Retornar período baseado na config
            period = config.get("main_screen_period", "3m")
            if period == "1m":
                return 30
            elif period == "3m":
                return 90
            elif period == "1y":
                return 365
            else:
                return None  # deck_life
                
        def _revlogLimit(self):
            if not self._deck_id:
                return ""
            # Incluir subdecks
            child_decks = [self._deck_id]
            for name, did in self.col.decks.children(self._deck_id):
                child_decks.append(did)
            deck_ids_str = ids2str(child_decks)
            return f"cid IN (SELECT id FROM cards WHERE did IN {deck_ids_str})"
            
        def _title(self, title, subtitle=""):
            return f'<h3 style="text-align: center; margin-bottom: 0.5em;">{title}</h3><p style="text-align: center; color: #666; margin-bottom: 1em; font-size: 0.9em;">{subtitle}</p>'
            
        def _graph(self, id, data, conf, ylabel=""):
            height = config.get("main_screen_height", 250)
            
            try:
                series_json = json.dumps(data)
                options_json = json.dumps(conf)
            except Exception:
                return "<div style='color:red;text-align:center;'>Erro ao processar dados do gráfico</div>"
            
            # Remover tickFormatter do JSON (será adicionado via JS)
            conf_for_json = conf.copy()
            if 'xaxis' in conf_for_json and 'tickFormatter' in conf_for_json['xaxis']:
                tick_formatter_js = conf_for_json['xaxis']['tickFormatter']
                del conf_for_json['xaxis']['tickFormatter']
                options_json = json.dumps(conf_for_json)
            else:
                tick_formatter_js = "function(val, axis) { return val.toFixed(0); }"
            
            return f'''
<div class="accumulated-retention-graph" style="margin: 1em 0; padding: 1em; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9;">
    <div id="{id}" style="height:{height}px; width:95%; margin: 0 auto;"></div>
    <p style="text-align: center; font-size: 0.8em; color: #666; margin-top: 0.5em;">{ylabel}</p>
</div>

<script type="text/javascript">
(function() {{
    if (typeof $ === 'undefined' || typeof $.plot === 'undefined') {{
        console.warn("Accumulated Graph: jQuery ou Flot não disponível");
        $("#{id}").html("<p style='color:#888; text-align:center;'>Gráfico não disponível</p>");
        return;
    }}

    $(function() {{
        try {{
            var data = {series_json};
            var options = {options_json};
            
            // Adicionar tickFormatter
            options.xaxis.tickFormatter = {tick_formatter_js};
            
            $.plot($("#{id}"), data, options);
        }} catch (e) {{
            console.error("Accumulated Graph: Erro:", e);
            $("#{id}").html("<p style='color:red; text-align:center;'>Erro ao renderizar gráfico</p>");
        }}
    }});
}})();
</script>
'''

    try:
        # Criar instância mock e gerar o gráfico usando a lógica existente
        mock_stats = MockCollectionStats(mw.col, deck_id)
        graph_html = render_card_evolution_graph(mock_stats)
        
        if graph_html and "No review data found" not in graph_html:
            content.body += graph_html
        elif config.get("show_no_data_message", False):
            content.body += f"<div style='text-align:center;margin:1em 0;color:#666;'>{tr('graph_no_data')}</div>"
            
    except Exception as e:
        print(f"Accumulated Graph Main Screen: Erro: {e}")

def init_main_screen_integration():
    """Inicializar integração com a tela principal."""
    config = mw.addonManager.getConfig(__name__)
    
    # Só registrar hooks se a funcionalidade estiver habilitada
    if config.get("enable_main_screen", False):
        overview_will_render_content.append(inject_graph_into_main_screen)
        deck_browser_will_render_content.append(inject_graph_into_main_screen)
        print("Accumulated Retention Graph: Integração com tela principal ativada")

# Chame esta função no final do seu __init__.py
# init_main_screen_integration() 