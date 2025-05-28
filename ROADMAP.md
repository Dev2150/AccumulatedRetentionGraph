# Roadmap do Accumulated Retention Graph

O objetivo é criar um gráfico que mostre a evolução do número de cartões e o estado deles (Aprendendo, Jovem, Maduro, Retido) ao longo do tempo, desde o início dos estudos do usuário até o dia atual (ou um período selecionado). A ideia é que, mesmo em dias sem estudo, o gráfico mantenha o estado anterior dos cartões, refletindo um crescimento cumulativo e a "maturação" da coleção de cartões.

## Funcionamento Detalhado do Gráfico:

1.  **Coleta de Dados Base:**
    *   Identificar a data de início relevante (seja a primeira revisão do usuário, ou o início do período selecionado como "1 mês", "1 ano") e a data final (normalmente "hoje").
    *   Carregar todas as entradas da tabela `revlog` do Anki que caem dentro do período relevante e, se aplicável, filtradas pelo deck selecionado. Cada entrada contém o ID do cartão (`cid`), o momento da revisão (`id` - timestamp), o tipo de revisão (`type` - learn, review, relearn, cram), e o intervalo resultante (`ivl`).

2.  **Processamento Dia a Dia (Simulado) Dentro do Período Selecionado:**
    *   O sistema irá iterar dia por dia, desde a data de início até a data de fim do período selecionado.
    *   Para cada dia `D` nesse intervalo:
        *   **Identificar Cartões Ativos:** Serão considerados todos os cartões que tiveram *pelo menos uma revisão até o final do dia `D`* (levando em conta todo o histórico do cartão, mesmo que anterior ao início do período do gráfico, para determinar o estado inicial corretamente).
        *   **Determinar o Estado de Cada Cartão Ativo no Dia `D`:** Para cada cartão ativo, o sistema encontrará a *última revisão registrada para ele até o final do dia `D`*. Com base no tipo (`type`) e no intervalo (`ivl`) dessa última revisão, o cartão será classificado em uma das seguintes categorias (os limites de intervalo exatos podem ser configuráveis ou baseados em padrões comuns do Anki, como na imagem de exemplo):
            *   **Aprendendo:** Cartões recém-introduzidos, em fase de aprendizado inicial, ou que foram errados recentemente e voltaram para essa fase. (Ex: `type` é aprendizado/reaprendizado, ou `ivl <= 7 dias`).
            *   **Jovens:** Cartões que já passaram da fase inicial de aprendizado mas ainda não têm intervalos longos. (Ex: `7 < ivl <= 21 dias`).
            *   **Maduros:** Cartões com intervalos estabelecidos, indicando boa retenção. (Ex: `21 < ivl <= 84 dias`).
            *   **Retidos (ou Sólidos/Well-Maintained):** Cartões com intervalos muito longos, indicando excelente retenção a longo prazo. (Ex: `ivl > 84 dias`).
        *   **Contagem Diária:** O sistema contará quantos cartões se enquadram em cada categoria para o dia `D`.

3.  **Construção do Gráfico:**
    *   **Eixo X (Tempo):** Representará os dias dentro do período selecionado (ex: "-30d", "-29d", ..., "0d").
    *   **Eixo Y (Quantidade):** Representará o número de cartões.
    *   **Barras Empilhadas:** Para cada dia no eixo X, uma barra vertical será desenhada. A altura total dessa barra representará o número total de cartões únicos que foram estudados *pelo menos uma vez até aquele dia* e que ainda estão ativos no escopo (coleção/deck).
    *   **Segmentos da Barra:** Cada barra será dividida em segmentos coloridos, onde cada cor representa uma categoria (Aprendendo, Jovem, Maduro, Retido), e a altura do segmento corresponde à quantidade de cartões naquela categoria naquele dia específico. As cores devem seguir uma progressão lógica, como na imagem de exemplo.

## Comportamento e Características:

*   **Estagnação Visual:** Se não houver estudos em um determinado dia (ou período), o gráfico para esses dias mostrará barras idênticas às do último dia com atividade ou mudança de estado, pois o estado cumulativo dos cartões não se alterou.
*   **Evolução Contínua:** Quando um cartão é estudado e seu intervalo/status muda, o gráfico refletirá essa mudança a partir do dia da revisão.
*   **Visão Cumulativa:** Diferente de gráficos que mostram apenas a atividade de um dia específico, este gráfico apresentará uma visão do *estado acumulado* da coleção de cartões ao longo do tempo.

## Adaptação aos Filtros Nativos do Anki:

O gráfico deve ser dinâmico e responder aos filtros de período e escopo do Anki:

*   **Filtro de Período (1 month, 1 year, deck life/collection life):**
    *   **"1 month":** O gráfico mostrará a evolução dos últimos 30 dias. O estado inicial dos cartões no primeiro dia do gráfico (-30d) será calculado com base em todas as revisões até aquele ponto.
    *   **"1 year":** O gráfico mostrará a evolução dos últimos 365 dias. Similarmente, o estado inicial em -365d considerará o histórico anterior.
    *   **"deck life" / "collection life":** O gráfico mostrará a evolução desde a primeira revisão registrada (para o deck ou coleção inteira) até o dia atual.
*   **Filtro de Escopo (deck, collection):**
    *   **"deck":** A análise e contagem de cartões serão restritas apenas aos cartões pertencentes ao deck atualmente selecionado nas estatísticas.
    *   **"collection":** A análise abrangerá todos os cartões da coleção.

A consulta SQL para buscar os dados da `revlog` e o processamento subsequente precisarão ser ajustados dinamicamente com base nesses filtros selecionados pelo usuário na interface de estatísticas do Anki. 