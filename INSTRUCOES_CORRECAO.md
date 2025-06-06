### Assunto: Padronizar Aparência do Gráfico entre a Página Inicial (Deck Browser) e a Visão Geral do Baralho (Overview)

**Análise do Problema:**

A legenda do gráfico de retenção apresentava uma aparência diferente ao comparar a página inicial (listagem de todos os baralhos) com a visão geral de um baralho específico. A análise do código revelou a causa:

1.  **Página Inicial (Deck Browser):** Usava o método `_graph()` customizado da classe `CompleteCollectionStats`
2.  **Visão Geral do Baralho (Overview):** Usava o método `_graph()` nativo do Anki (`stats.CollectionStats`)

Essa diferença na implementação fazia com que os gráficos tivessem aparências inconsistentes entre as duas telas.

**Solução Implementada:**

A correção foi padronizar ambos os gráficos para usar o **método customizado** da classe `CompleteCollectionStats`, que oferece melhor controle e aparência mais consistente.

**Modificações Realizadas no arquivo `__init__.py`:**

---

#### 1. Padronização da Legenda:

-   **Localização:** Função `get_card_evolution_data`
-   **Modificação:** Adicionadas configurações explícitas de fundo na legenda do gráfico Flot.

**Aplicado:**
```python
# ... em graph_options
"legend": {
    "show": True,
    "position": "nw",
    "backgroundColor": "rgb(245, 245, 245)",
    "backgroundOpacity": 0.85
}
```

---

#### 2. Remoção da "Borda Extra":

-   **Localização:** Função `_render_main_screen_graph_html`
-   **Modificação:** Removido estilo desnecessário do contêiner que envolve o gráfico.

**Aplicado:**
```python
return f'<div class="evolution-graph-main-wrapper" style="max-width: 900px; margin: 20px auto;">{graph_html}</div>'
```

---

#### 3. Padronização do Método de Renderização:

-   **Localização:** Função `render_card_evolution_graph`
-   **Modificação:** Alterada para usar a classe customizada `CompleteCollectionStats` em ambas as telas.

**Aplicado:**
```python
def render_card_evolution_graph(self_instance):
    # ... código existente ...
    
    # Criar uma instância customizada para usar o método _graph padronizado
    custom_stats = CompleteCollectionStats(self_instance.col)
    
    # Usar o método _title da instância customizada
    html = custom_stats._title(title, subtitle)
    html += custom_stats._graph(
        id=graph_id,
        data=series_data,
        conf=options,
        ylabel=tr("graph_y_label")
    )
    html += tooltip_html
    return html
```

---

**Resultado:**
- Ambas as telas (página inicial e visão geral do baralho) agora usam exatamente o mesmo método de renderização
- O gráfico tem aparência 100% idêntica e integrada em ambas as telas
- A interface ficou mais limpa e consistente
- A legenda tem sempre o mesmo fundo semi-transparente, independente da tela 
---

#### 4. Correção Adicional: Restauração do Tooltip Detalhado

-   **Problema Identificado:** Durante as refatorações para padronizar as telas, o script do tooltip (a caixa de informações que aparece ao passar o mouse sobre o gráfico) foi acidentalmente substituído por uma versão excessivamente simples. A funcionalidade que exibia o detalhamento de cartões por categoria (Retidos, Maduros, Jovens, etc.) para cada ponto no tempo foi perdida.

-   **Solução Implementada:**
    -   **Localização:** Função `get_card_evolution_data`
    -   **Modificação:** O script original e detalhado do tooltip foi restaurado. Este script mais complexo itera sobre todas as séries de dados do gráfico para um ponto específico no tempo, coletando e exibindo a contagem para cada categoria individualmente, além do total.
    -   Também foram adicionadas variáveis para passar todas as strings de tradução necessárias do Python para o JavaScript, garantindo que o tooltip funcione corretamente em diferentes idiomas.

-   **Resultado:**
    -   O tooltip voltou a exibir o resumo completo e detalhado, mostrando a contagem de cartões para cada estágio de aprendizado ao passar o mouse sobre o gráfico, como era a intenção original. 