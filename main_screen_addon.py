# -*- coding: utf-8 -*-
"""
Accumulated Retention Graph - Main Screen Port
Porta o gráfico de Accumulated Retention para a tela principal do Anki.
"""

import math
import json
from typing import Any, Optional, Tuple, Dict, List

from anki.collection import Collection
from anki.utils import ids2str
from aqt import mw
from aqt.gui_hooks import (
    overview_will_render_content,
    deck_browser_will_render_content,
)
from aqt.overview import OverviewContent
from aqt.deckbrowser import DeckBrowserContent

# Tentar importar traduções do addon original
try:
    from .translations import tr
except ImportError:
    # Fallback se não encontrar o módulo de traduções
    def tr(key, **kwargs):
        translations = {
            "label_retained": "Retidos (>84 dias)",
            "label_mature": "Maduros (>21 dias)", 
            "label_young": "Jovens (>7 dias)",
            "label_learning": "Aprendendo",
            "label_today": "Hoje",
            "tooltip_period": "Período: ",
            "tooltip_total": "Total: ",
            "graph_title": "Retenção Acumulada",
            "graph_subtitle": "Quantidade de cartões por estado ao longo do tempo",
            "graph_no_data": "Nenhum dado de revisão encontrado",
            "graph_y_label": "Nº de Cartões"
        }
        return translations.get(key, key.replace("_", " ").title())

# Constantes de categorização
CAT_LEARNING = 0
CAT_YOUNG = 1
CAT_MATURE = 2
CAT_RETAINED = 3

# Cores padrão - podem ser personalizadas via config
DEFAULT_COLORS = {
    CAT_LEARNING: "#FFA500",  # Laranja
    CAT_YOUNG: "#90EE90",     # Verde Claro
    CAT_MATURE: "#008000",    # Verde Escuro
    CAT_RETAINED: "#004080"   # Azul Escuro
}

# Limiares de intervalo em dias
INTERVAL_LEARNING_MAX = 7
INTERVAL_YOUNG_MAX = 21
INTERVAL_MATURE_MAX = 84

def get_config():
    """Obter configuração do addon com fallbacks seguros."""
    try:
        config = mw.addonManager.getConfig(__name__)
        if config:
            return config
    except:
        pass
    
    # Configuração padrão
    return {
        "hide_learning": False,
        "hide_young": False,
        "hide_mature": False,
        "hide_retained": False,
        "exclude_deleted_cards": True,
        "main_screen_period": "3m",  # Período padrão para tela principal
        "main_screen_height": 250,   # Altura do gráfico em pixels
        "show_in_overview": True,    # Mostrar na visão geral do deck
        "show_in_deck_browser": True # Mostrar no navegador de decks
    }

def get_card_category(revlog_type, last_interval_days):
    """Categorizar cartão baseado no tipo de revisão e intervalo."""
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
    return CAT_LEARNING

def get_evolution_data(
    col: Collection,
    period_key: str = "3m",
    deck_id: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
    """
    Coleta e processa dados de evolução dos cartões.
    
    Args:
        col: Coleção do Anki
        period_key: Período ("1m", "3m", "1y", "deck_life")
        deck_id: ID do deck (None para toda coleção)
    
    Returns:
        Tuple com (series_data, graph_options, tooltip_html)
    """
    if not col or not col.sched or not col.db:
        return [], {}, ""

    # Configurar período e agregação
    period_config = {
        "1m": {"days": 30, "chunk": 1, "suffix": "d"},
        "3m": {"days": 90, "chunk": 7, "suffix": "w"},
        "1y": {"days": 365, "chunk": 30, "suffix": "m"},
        "deck_life": {"days": None, "chunk": 30, "suffix": "m"}
    }
    
    config = period_config.get(period_key, period_config["3m"])
    period_days = config["days"]
    aggregation_chunk_days = config["chunk"]
    unit_suffix = config["suffix"]

    try:
        day_cutoff_s = col.sched.day_cutoff
    except AttributeError:
        return [], {}, ""

    end_date_timestamp_ms = day_cutoff_s * 1000
    
    # Construir filtros SQL
    conditions = [f"id < {end_date_timestamp_ms}"]
    
    if deck_id:
        # Incluir subdecks
        child_decks = [deck_id]
        for name, did in col.decks.children(deck_id):
            child_decks.append(did)
        deck_ids_str = ids2str(child_decks)
        conditions.append(f"cid IN (SELECT id FROM cards WHERE did IN {deck_ids_str})")
    
    # Configuração do addon
    addon_config = get_config()
    if addon_config.get("exclude_deleted_cards", True):
        conditions.append("cid IN (SELECT id FROM cards)")

    # Determinar data de início
    if period_days is not None:
        graph_start_day_idx = -(period_days - 1)
    else:  # deck_life
        first_rev_query = "SELECT MIN(id) FROM revlog"
        if len(conditions) > 1:
            first_rev_query += f" WHERE {' AND '.join(conditions[1:])}"
        min_revlog_id_ms = col.db.scalar(first_rev_query)
        if not min_revlog_id_ms:
            return [], {}, ""
        days_ago = (day_cutoff_s - (min_revlog_id_ms / 1000)) // 86400
        graph_start_day_idx = -int(days_ago)

    # Buscar dados de revisão
    query = f"""
        SELECT id, cid, type, ivl
        FROM revlog
        WHERE {' AND '.join(conditions)}
        ORDER BY id ASC
    """
    
    all_reviews = col.db.all(query)
    if not all_reviews:
        return [], {}, ""

    # Processar dados dia a dia
    card_states = {}
    daily_data = {}
    
    # Inicializar estrutura de dados
    for i in range(graph_start_day_idx, 1):
        daily_data[i] = {CAT_LEARNING: 0, CAT_YOUNG: 0, CAT_MATURE: 0, CAT_RETAINED: 0}

    # Processar revisões por dia
    current_rev_idx = 0
    for day_offset in range(graph_start_day_idx, 1):
        current_day_end_ms = (day_cutoff_s + (day_offset * 86400)) * 1000
        if day_offset == 0:
            current_day_end_ms = end_date_timestamp_ms
        
        # Processar todas as revisões até o final do dia
        while current_rev_idx < len(all_reviews):
            rev_id_ms, cid, rev_type, rev_ivl = all_reviews[current_rev_idx]
            if rev_id_ms < current_day_end_ms:
                category = get_card_category(rev_type, rev_ivl)
                card_states[cid] = {
                    'category': category,
                    'last_rev_time': rev_id_ms
                }
                current_rev_idx += 1
            else:
                break
        
        # Contar cartões por categoria no final do dia
        day_counts = {CAT_LEARNING: 0, CAT_YOUNG: 0, CAT_MATURE: 0, CAT_RETAINED: 0}
        for card_id, state in card_states.items():
            if state['last_rev_time'] < current_day_end_ms:
                day_counts[state['category']] += 1
        
        daily_data[day_offset] = day_counts

    # Agregar dados em chunks
    aggregated_data = {CAT_LEARNING: {}, CAT_YOUNG: {}, CAT_MATURE: {}, CAT_RETAINED: {}}
    
    for day_idx in sorted(daily_data.keys()):
        chunk_idx = -math.floor(-day_idx / aggregation_chunk_days)
        current_counts = daily_data[day_idx]
        
        # Usar última contagem do chunk (mais recente)
        for category in [CAT_LEARNING, CAT_YOUNG, CAT_MATURE, CAT_RETAINED]:
            aggregated_data[category][chunk_idx] = current_counts[category]

    # Preparar séries para o gráfico
    series = []
    all_chunks = sorted(set().union(*[data.keys() for data in aggregated_data.values()]))
    
    if not all_chunks:
        return [], {}, ""

    # Criar dados das séries
    series_info = [
        (CAT_RETAINED, "label_retained", DEFAULT_COLORS[CAT_RETAINED], 1),
        (CAT_MATURE, "label_mature", DEFAULT_COLORS[CAT_MATURE], 2),
        (CAT_YOUNG, "label_young", DEFAULT_COLORS[CAT_YOUNG], 3),
        (CAT_LEARNING, "label_learning", DEFAULT_COLORS[CAT_LEARNING], 4)
    ]
    
    for category, label_key, color, order in series_info:
        if not addon_config.get(f"hide_{label_key.split('_')[1]}", False):
            data_points = []
            for chunk_idx in all_chunks:
                value = aggregated_data[category].get(chunk_idx, 0)
                data_points.append([chunk_idx, value])
            
            series.append({
                "data": data_points,
                "label": tr(label_key),
                "color": color,
                "bars": {"order": order},
                "stack": True
            })

    # Configurar eixos
    min_x = min(all_chunks) - 0.5
    max_x = max(max(all_chunks), 0) + 0.5

    # Opções do gráfico
    graph_options = {
        "xaxis": {
            "min": min_x,
            "max": max_x,
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
                "barWidth": 0.9,
                "lineWidth": 1,
                "fill": 0.8
            }
        },
        "grid": {"hoverable": True, "clickable": True, "borderColor": "#C0C0C0"},
        "legend": {"show": True, "position": "nw"}
    }

    # HTML do tooltip
    tooltip_html = f'<div id="accumulatedGraphTooltip" style="position:absolute;display:none;padding:5px;border:1px solid #333;background-color:#f5f5f5;opacity:0.9;color:#000;"></div>'

    return series, graph_options, tooltip_html

def generate_graph_html(
    graph_id: str,
    series_data: List[Dict[str, Any]],
    graph_options: Dict[str, Any],
    tooltip_html: str
) -> str:
    """Gera HTML completo do gráfico."""
    
    if not series_data:
        return f"<div style='text-align:center;margin:1em 0;'>{tr('graph_no_data')}</div>"

    config = get_config()
    height = config.get("main_screen_height", 250)
    
    try:
        series_json = json.dumps(series_data)
        options_json = json.dumps(graph_options)
    except Exception:
        return "<div style='color:red;text-align:center;'>Erro ao processar dados do gráfico</div>"

    # Função JavaScript para formatação do eixo X
    unit_suffix = graph_options.get("xaxis", {}).get("unit_suffix", "d")
    aggregation_days = graph_options.get("xaxis", {}).get("aggregation_chunk_days", 1)
    tr_today = tr("label_today")

    html = f'''
<div class="accumulated-retention-graph" style="margin: 1em 0; padding: 1em; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9;">
    <h3 style="text-align: center; margin-bottom: 0.5em;">{tr("graph_title")}</h3>
    <p style="text-align: center; color: #666; margin-bottom: 1em; font-size: 0.9em;">{tr("graph_subtitle")}</p>
    <div id="{graph_id}" style="height:{height}px; width:95%; margin: 0 auto;"></div>
    <p style="text-align: center; font-size: 0.8em; color: #666; margin-top: 0.5em;">{tr("graph_y_label")}</p>
</div>

{tooltip_html}

<script type="text/javascript">
(function() {{
    if (typeof $ === 'undefined' || typeof $.plot === 'undefined') {{
        console.warn("Accumulated Graph: jQuery ou Flot não disponível");
        $("#{graph_id}").html("<p style='color:#888; text-align:center;'>Gráfico não disponível (dependências JS em falta)</p>");
        return;
    }}

    $(function() {{
        try {{
            var data = {series_json};
            var options = {options_json};

            // Configurar formatação do eixo X
            options.xaxis.tickFormatter = function(val, axis) {{
                var suffix = '{unit_suffix}';
                var aggDays = {aggregation_days};
                if (aggDays === 1 && Math.abs(val - 0) < 0.001) {{
                    return '{tr_today}';
                }}
                var decimals = axis.options.tickDecimals || 0;
                return val.toFixed(decimals) + suffix;
            }};

            // Plotar gráfico
            var plot = $.plot($("#{graph_id}"), data, options);

            // Configurar tooltip
            var tooltip = $("#accumulatedGraphTooltip");
            if (!tooltip.length) {{
                tooltip = $('<div id="accumulatedGraphTooltip" style="position:absolute;display:none;padding:5px;border:1px solid #333;background-color:#f5f5f5;opacity:0.9;color:#000;"></div>').appendTo("body");
            }}

            $("#{graph_id}").bind("plothover", function(event, pos, item) {{
                if (item) {{
                    var x_val = item.datapoint[0];
                    var plot_data = plot.getData();
                    var point_data = {{}};
                    var total = 0;

                    // Coletar dados de todas as séries para este ponto
                    for (var i = 0; i < plot_data.length; i++) {{
                        var series = plot_data[i];
                        for (var j = 0; j < series.data.length; j++) {{
                            var point = series.data[j];
                            if (Math.abs(point[0] - x_val) < 0.001) {{
                                point_data[series.label] = point[1];
                                total += point[1];
                                break;
                            }}
                        }}
                    }}

                    // Formatar título
                    var title;
                    if ({aggregation_days} === 1 && Math.abs(x_val - 0) < 0.001) {{
                        title = '{tr_today}';
                    }} else {{
                        title = x_val.toFixed(0) + '{unit_suffix}';
                    }}

                    // Montar conteúdo do tooltip
                    var content = "<b>{tr('tooltip_period')}" + title + "</b><br/>";
                    
                    var labels = ["{tr('label_retained')}", "{tr('label_mature')}", "{tr('label_young')}", "{tr('label_learning')}"];
                    for (var k = 0; k < labels.length; k++) {{
                        var label = labels[k];
                        if (point_data[label] !== undefined) {{
                            content += label + ": " + point_data[label] + "<br/>";
                        }}
                    }}
                    content += "<b>{tr('tooltip_total')}" + total + "</b>";

                    tooltip.html(content)
                           .css({{top: item.pageY + 5, left: item.pageX + 5}})
                           .fadeIn(200);
                }} else {{
                    tooltip.hide();
                }}
            }});

        }} catch (e) {{
            console.error("Accumulated Graph: Erro ao renderizar:", e);
            $("#{graph_id}").html("<p style='color:red; text-align:center;'>Erro ao renderizar gráfico</p>");
        }}
    }});
}})();
</script>
'''
    return html

def inject_graph_into_content(content: Any, context: Any) -> None:
    """Injeta o gráfico no conteúdo da tela principal."""
    if not mw or not mw.col:
        return

    config = get_config()
    
    # Verificar se deve mostrar baseado no tipo de tela
    if isinstance(context, OverviewContent) and not config.get("show_in_overview", True):
        return
    elif isinstance(context, DeckBrowserContent) and not config.get("show_in_deck_browser", True):
        return

    # Determinar deck_id e período
    deck_id = None
    period_key = config.get("main_screen_period", "3m")
    graph_id_suffix = "main"

    # Tentar obter deck_id do contexto
    if isinstance(context, OverviewContent):
        # Pegar deck atual da overview
        if hasattr(mw, 'overview') and hasattr(mw.overview, 'deck'):
            current_deck = mw.overview.deck
            if current_deck:
                deck_id = current_deck['id']
                graph_id_suffix = f"overview_{deck_id}"
        elif hasattr(mw.col, 'decks') and hasattr(mw.col.decks, 'current'):
            current_deck = mw.col.decks.current()
            if current_deck:
                deck_id = current_deck['id']
                graph_id_suffix = f"deck_{deck_id}"
    elif isinstance(context, DeckBrowserContent):
        # Na tela do navegador de decks, usar toda a coleção
        deck_id = None
        graph_id_suffix = "browser"

    graph_id = f"accumulatedGraph_{graph_id_suffix}"

    try:
        # Gerar dados do gráfico
        series, options, tooltip_html = get_evolution_data(
            col=mw.col,
            period_key=period_key,
            deck_id=deck_id
        )

        if series:
            # Gerar HTML do gráfico
            graph_html = generate_graph_html(graph_id, series, options, tooltip_html)
            # Adicionar ao final do corpo
            content.body += graph_html
        else:
            # Opcional: mostrar mensagem quando não há dados
            if config.get("show_no_data_message", False):
                content.body += f"<div style='text-align:center;margin:1em 0;color:#666;'>{tr('graph_no_data')}</div>"

    except Exception as e:
        print(f"Accumulated Graph: Erro ao gerar gráfico: {e}")
        # Em produção, pode ser melhor não mostrar erro para o usuário
        # content.body += f"<div style='color:red; text-align:center;'>Erro: {e}</div>"

def init_main_screen_hooks():
    """Inicializa os hooks para injetar o gráfico na tela principal."""
    overview_will_render_content.append(inject_graph_into_content)
    deck_browser_will_render_content.append(inject_graph_into_content)

# Inicializar hooks automaticamente quando o módulo for carregado
init_main_screen_hooks() 