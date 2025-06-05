### Configuration

You can customize the addon's behavior by editing the `config.json` file within the addon's folder. The available options are also described in `config.md`:

#### Statistics Screen Options
-   `hide_learning` (boolean): If `true`, the "Learning" section in the stacked bar graph is not shown. Default: `false`.
-   `hide_young` (boolean): If `true`, the "Young" section is not shown. Default: `false`.
-   `hide_mature` (boolean): If `true`, the "Mature" section is not shown. Default: `false`.
-   `hide_retained` (boolean): If `true`, the "Retained" section is not shown. Default: `false`.
-   `show_at_beginning` (boolean): If `true`, the evolution graph will be displayed *before* Anki's default card statistics graph (on the statistics screen). If `false`, it will be displayed *after*. Default: `false`.
-   `exclude_deleted_cards` (boolean): If `true`, reviews from cards that were later deleted are excluded from the graph. Default: `true`.

#### Main Screen Options (NEW!)
-   `enable_main_screen` (boolean): If `true`, enables the graph on Anki's main screen (overview and deck browser). Default: `false`.
-   `main_screen_period` (string): Default period for main screen graph. Options: "1m", "3m", "1y", "deck_life". Default: `"3m"`.
-   `main_screen_height` (integer): Height of the graph in pixels on main screen. Default: `250`.
-   `show_in_overview` (boolean): If `true`, shows the graph in deck overview screen. Default: `true`.
-   `show_in_deck_browser` (boolean): If `true`, shows the graph in deck browser screen. Default: `true`.
-   `show_no_data_message` (boolean): If `true`, shows a message when no data is available. Default: `false`.

(The `translation_maps` key in `config.json` is used for internationalization and should generally not be modified unless you are adding new translations.)

### Configuração

Você pode customizar o comportamento do addon editando o arquivo `config.json` dentro da pasta do addon. As opções disponíveis também são descritas em `config.md`:

#### Opções da Tela de Estatísticas
-   `hide_learning` (booleano): Se `true`, a seção "Aprendendo" no gráfico de barras empilhadas não é mostrada. Padrão: `false`.
-   `hide_young` (booleano): Se `true`, a seção "Jovem" não é mostrada. Padrão: `false`.
-   `hide_mature` (booleano): Se `true`, a seção "Maduro" não é mostrada. Padrão: `false`.
-   `hide_retained` (booleano): Se `true`, a seção "Retido" não é mostrada. Padrão: `false`.
-   `show_at_beginning` (booleano): Se `true`, o gráfico de evolução será exibido *antes* do gráfico de estatísticas padrão do Anki (na tela de estatísticas). Se `false`, será exibido *depois*. Padrão: `false`.
-   `exclude_deleted_cards` (booleano): Se `true`, revisões de cartões que foram posteriormente deletados são excluídas do gráfico. Padrão: `true`.

#### Opções da Tela Principal (NOVO!)
-   `enable_main_screen` (booleano): Se `true`, habilita o gráfico na tela principal do Anki (visão geral e navegador de decks). Padrão: `false`.
-   `main_screen_period` (string): Período padrão para o gráfico da tela principal. Opções: "1m", "3m", "1y", "deck_life". Padrão: `"3m"`.
-   `main_screen_height` (integer): Altura do gráfico em pixels na tela principal. Padrão: `250`.
-   `show_in_overview` (booleano): Se `true`, mostra o gráfico na tela de visão geral do deck. Padrão: `true`.
-   `show_in_deck_browser` (booleano): Se `true`, mostra o gráfico na tela do navegador de decks. Padrão: `true`.
-   `show_no_data_message` (booleano): Se `true`, mostra uma mensagem quando não há dados disponíveis. Padrão: `false`.

(A chave `translation_maps` em `config.json` é usada para internacionalização e geralmente não deve ser modificada, a menos que você esteja adicionando novas traduções.)
