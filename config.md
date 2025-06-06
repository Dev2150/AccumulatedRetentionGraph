## Configuration

### Statistics Screen Options
- `hide_learning` (boolean): If `true`, the "Learning" section in the stacked bar graph is not shown. Default: `false`.
- `hide_young` (boolean): If `true`, the "Young" section is not shown. Default: `false`.
- `hide_mature` (boolean): If `true`, the "Mature" section is not shown. Default: `false`.
- `hide_retained` (boolean): If `true`, the "Retained" section is not shown. Default: `false`.
- `show_at_beginning` (boolean): If `true`, the graph will be displayed before Anki's default statistics. Default: `false`.
- `exclude_deleted_cards` (boolean): If `true`, reviews from deleted cards are excluded. Default: `true`.
- `use_absolute_dates` (boolean): If `true`, shows absolute dates instead of relative days. Default: `true`.

### Main Screen Options
- `enable_main_screen` (boolean): If `true`, enables the graph on Anki's main screen. Default: `true`.
- `main_screen_period` (string): Default period for main screen graph. Options: "1m", "3m", "1y", "deck_life", or custom periods like "6m", "9m", "2y". Default: `"3m"`.
- `main_screen_aggregation` (string): Aggregation level for main screen graph. Options: "d" (daily), "w" (weekly). Default: `"d"`.
- `main_screen_height` (integer): Height of the graph in pixels on main screen. Default: `250`.
- `show_in_overview` (boolean): If `true`, shows the graph in deck overview screen. Default: `true`.
- `show_in_deck_browser` (boolean): If `true`, shows the graph in deck browser screen. Default: `true`.

### Translation
- `translation_maps` (object): Contains translations for different languages. Generally should not be modified unless adding new translations.

---

## Configuração

Você pode personalizar o comportamento do addon editando o arquivo `config.json` na pasta do addon.

### Opções da Tela de Estatísticas
- `hide_learning` (booleano): Se `true`, a seção "Aprendendo" não é mostrada. Padrão: `false`.
- `hide_young` (booleano): Se `true`, a seção "Jovem" não é mostrada. Padrão: `false`.
- `hide_mature` (booleano): Se `true`, a seção "Maduro" não é mostrada. Padrão: `false`.
- `hide_retained` (booleano): Se `true`, a seção "Retido" não é mostrada. Padrão: `false`.
- `show_at_beginning` (booleano): Se `true`, o gráfico será exibido antes das estatísticas padrão do Anki. Padrão: `false`.
- `exclude_deleted_cards` (booleano): Se `true`, revisões de cartões deletados são excluídas. Padrão: `true`.
- `use_absolute_dates` (booleano): Se `true`, mostra datas absolutas em vez de dias relativos. Padrão: `true`.

### Opções da Tela Principal
- `enable_main_screen` (booleano): Se `true`, habilita o gráfico na tela principal do Anki. Padrão: `true`.
- `main_screen_period` (string): Período padrão para o gráfico da tela principal. Opções: "1m", "3m", "1y", "deck_life", ou períodos customizados como "6m", "9m", "2y". Padrão: `"3m"`.
- `main_screen_aggregation` (string): Nível de agregação para o gráfico da tela principal. Opções: "d" (diário), "w" (semanal). Padrão: `"d"`.
- `main_screen_height` (integer): Altura do gráfico em pixels na tela principal. Padrão: `250`.
- `show_in_overview` (booleano): Se `true`, mostra o gráfico na tela de visão geral do deck. Padrão: `true`.
- `show_in_deck_browser` (booleano): Se `true`, mostra o gráfico na tela do navegador de decks. Padrão: `true`.

### Tradução
- `translation_maps` (objeto): Contém traduções para diferentes idiomas. Geralmente não deve ser modificado, exceto para adicionar novas traduções.
