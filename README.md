# **Accumulated Retention Graph**

> **Note:** This document is available in both English and Portuguese. The English version is presented first, followed by the Portuguese version.
>
> **Nota:** Este documento está disponível em inglês e português. A versão em inglês é apresentada primeiro, seguida pela versão em português.

---

<p align="center">
  *Anki's statistics screen with the "Accumulated Retention Graph" add-on installed:*/<br>
  *Tela de estatísticas do Anki com o add-on "Accumulated Retention Graph" instalado:*
  <br>
  <img src="https://i.ibb.co/FbbxVvxp/image.png" alt="Screenshot of Accumulated Retention Graph">
</p>

## **English**

### What is Accumulated Retention Graph?

Accumulated Retention Graph is an Anki addon that provides a visual representation of how your card learning states (Learning, Young, Mature, Retained) have evolved over time. It adds a new stacked bar graph to Anki's statistics screen, allowing you to see trends in your study habits and how your knowledge base is solidifying.

### How does it work?

- **Evolution Graph:** Displays a stacked bar chart showing the count of cards in each state (Learning, Young, Mature, Retained) for different time periods (1 month, 3 months, 1 year, or deck life).
- **Color-Coded States:**
    - **Blue (Retained):** Cards with intervals greater than 84 days.
    - **Dark Green (Mature):** Cards with intervals greater than 21 days and up to 84 days.
    - **Light Green (Young):** Cards with intervals greater than 7 days and up to 21 days.
    - **Orange (Learning):** Cards with intervals up to 7 days, or currently in learning/relearning phases.
- **Time Aggregation:** Data is aggregated by day, week, or month depending on the selected statistics period, making the graph easy to read.
- **Interactivity:**
    - Hover over a bar segment to see a detailed tooltip with counts for each category and the total for that specific period.
- **Customization:**
    - Choose to show or hide specific card states (Learning, Young, Mature, Retained) via the addon's configuration.
    - Option to display the evolution graph at the beginning or end of the standard card stats.

### Main benefits

- **Track Progress Over Time:** See how the distribution of your card states changes, indicating learning progression or areas needing more attention.
- **Identify Trends:** Understand if you are consistently maturing cards or if many are stuck in early learning phases.
- **Integrated View:** The graph is added directly to the existing Anki statistics screen for the current deck or entire collection.

### Configuration

You can customize the addon's behavior by editing the `config.json` file within the addon's folder (`zz_evolution`). The available options are also described in `config.md`:

-   `hide_learning` (boolean): If `true`, the "Learning" section in the stacked bar graph is not shown. Default: `false`.
-   `hide_young` (boolean): If `true`, the "Young" section is not shown. Default: `false`.
-   `hide_mature` (boolean): If `true`, the "Mature" section is not shown. Default: `false`.
-   `hide_retained` (boolean): If `true`, the "Retained" section is not shown. Default: `false`.
-   `show_at_beginning` (boolean): If `true`, the evolution graph will be displayed *before* Anki's default card statistics graph. If `false`, it will be displayed *after*. Default: `false`.

(The `translation_maps` key in `config.json` is used for internationalization and should generally not be modified unless you are adding new translations.)

### License and Contact

- **Copyright(C)** [Carlos Duarte]
- Licensed under [GNU AGPL, version 3](http://www.gnu.org/licenses/agpl.html)
- For bugs or suggestions, please open an issue at [https://github.com/cjdduarte/AccumulatedRetentionGraph/issues](https://github.com/cjdduarte/AccumulatedRetentionGraph/issues) (Note: This is a placeholder URL, please update it with your actual repository URL).

---

## **Português**

### O que é o Accumulated Retention Graph?

O Accumulated Retention Graph é um addon para o Anki que fornece uma representação visual de como os estados de aprendizado dos seus cartões (Aprendendo, Jovem, Maduro, Retido) evoluíram ao longo do tempo. Ele adiciona um novo gráfico de barras empilhadas à tela de estatísticas do Anki, permitindo que você veja tendências em seus hábitos de estudo e como sua base de conhecimento está se solidificando.

### Como funciona?

- **Gráfico de Evolução:** Exibe um gráfico de barras empilhadas mostrando a contagem de cartões em cada estado (Aprendendo, Jovem, Maduro, Retido) para diferentes períodos de tempo (1 mês, 3 meses, 1 ano ou vida útil do baralho).
- **Estados Codificados por Cores:**
    - **Azul (Retido):** Cartões com intervalos superiores a 84 dias.
    - **Verde Escuro (Maduro):** Cartões com intervalos superiores a 21 dias e até 84 dias.
    - **Verde Claro (Jovem):** Cartões com intervalos superiores a 7 dias e até 21 dias.
    - **Laranja (Aprendendo):** Cartões com intervalos de até 7 dias, ou atualmente nas fases de aprendizado/reaprendizado.
- **Agregação de Tempo:** Os dados são agregados por dia, semana ou mês, dependendo do período estatístico selecionado, tornando o gráfico fácil de ler.
- **Interatividade:**
    - Passe o mouse sobre um segmento da barra para ver uma dica de ferramenta detalhada com as contagens para cada categoria e o total para aquele período específico.
- **Customização:**
    - Escolha mostrar ou ocultar estados específicos dos cartões (Aprendendo, Jovem, Maduro, Retido) através da configuração do addon.
    - Opção para exibir o gráfico de evolução no início ou no final das estatísticas padrão dos cartões.

### Principais benefícios

- **Acompanhe o Progresso ao Longo do Tempo:** Veja como a distribuição dos estados dos seus cartões muda, indicando a progressão do aprendizado ou áreas que precisam de mais atenção.
- **Identifique Tendências:** Entenda se você está consistentemente maturando cartões ou se muitos estão presos nas fases iniciais de aprendizado.
- **Visão Integrada:** O gráfico é adicionado diretamente à tela de estatísticas existente do Anki para o baralho atual ou coleção inteira.

### Configuração

Você pode customizar o comportamento do addon editando o arquivo `config.json` dentro da pasta do addon (`zz_evolution`). As opções disponíveis também são descritas em `config.md`:

-   `hide_learning` (booleano): Se `true`, a seção "Aprendendo" no gráfico de barras empilhadas não é mostrada. Padrão: `false`.
-   `hide_young` (booleano): Se `true`, a seção "Jovem" não é mostrada. Padrão: `false`.
-   `hide_mature` (booleano): Se `true`, a seção "Maduro" não é mostrada. Padrão: `false`.
-   `hide_retained` (booleano): Se `true`, a seção "Retido" não é mostrada. Padrão: `false`.
-   `show_at_beginning` (booleano): Se `true`, o gráfico de evolução será exibido *antes* do gráfico de estatísticas padrão do Anki. Se `false`, será exibido *depois*. Padrão: `false`.

(A chave `translation_maps` em `config.json` é usada para internacionalização e geralmente não deve ser modificada, a menos que você esteja adicionando novas traduções.)

### Licença e Contato

- **Copyright(C)** [Carlos Duarte]
- Licenciado sob [GNU AGPL, version 3](http://www.gnu.org/licenses/agpl.html)
- For bugs or suggestions, please open an issue em [https://github.com/cjdduarte/AccumulatedRetentionGraph/issues](https://github.com/cjdduarte/AccumulatedRetentionGraph/issues) (Nota: Esta é uma URL de placeholder, por favor, atualize-a com a URL do seu repositório real).

## **Changelog**

- **v1.0 - 2025-05-28 - Initial version**
  - Displays a stacked bar graph of card states (Learning, Young, Mature, Retained) over time.
  - Data aggregation based on statistics period (1m, 3m, 1y, all).
  - Customizable visibility for each card state series.
  - Option to show the graph before or after Anki's default card stats.
  - Tooltip display for detailed counts on hover.
  - Basic internationalization for labels (English, Portuguese).
