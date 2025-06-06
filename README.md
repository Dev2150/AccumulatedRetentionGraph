# **Accumulated Retention Graph**

> **Note:** This document is available in English and Portuguese. The English version is presented first, followed by the Portuguese version.
>
> **Nota:** Este documento está disponível em inglês e português. A versão em inglês é apresentada primeiro, seguida pela versão em português.

---

<p align="center">
  <img src="https://i.ibb.co/1JPsLqjM/image.png" alt="Screenshot of Accumulated Retention Graph">
</p>

<p align="center">
  <img src="https://i.ibb.co/8Dkws9kr/image.png" alt="Additional Screenshot 1">
</p>

<p align="center">
  <img src="https://i.ibb.co/JRwpbCn8/image.png" alt="Additional Screenshot 2">
</p>

## **English**

### What is Accumulated Retention Graph?

Accumulated Retention Graph is an Anki addon that provides a visual representation of how your card learning states evolve over time. It displays stacked bar graphs showing the distribution of cards across different learning states (Learning, Young, Mature, Retained).

### Key Features

#### **Statistics Screen Integration**
- **Evolution Graph:** Stacked bar chart showing card counts for each state over time
- **Time Periods:** 1 month, 3 months, 1 year, or deck life
- **Data Aggregation:** By day, week, or month with absolute dates (e.g., "Oct 24")

#### **Main Screen Integration** *(NEW!)*
- **Overview Screen:** Graph displayed in deck overview
- **Deck Browser:** Graph displayed in deck browser screen
- **Customizable:** Configurable period, aggregation level, and height

#### **Card States & Colors**
- **Blue (Retained):** Cards with intervals > 84 days
- **Dark Green (Mature):** Cards with intervals 21-84 days  
- **Light Green (Young):** Cards with intervals 7-21 days
- **Orange (Learning):** Cards with intervals ≤ 7 days or in learning phases

#### **Interactive Features**
- **Tooltips:** Hover for detailed counts and totals
- **Customization:** Show/hide specific card states via configuration
- **Flexible Display:** Choose graph position and date format

### Benefits

- **Track Progress:** Monitor how card distributions change over time
- **Identify Patterns:** Understand learning progression and bottlenecks
- **Multiple Views:** Access graphs from statistics screen and main interface

---

## **Português**

### O que é o Accumulated Retention Graph?

O Accumulated Retention Graph é um addon para o Anki que fornece uma representação visual de como os estados de aprendizado dos seus cartões evoluem ao longo do tempo. Ele exibe gráficos de barras empilhadas mostrando a distribuição de cartões em diferentes estados de aprendizado (Aprendendo, Jovem, Maduro, Retido).

### Principais Funcionalidades

#### **Integração com Tela de Estatísticas**
- **Gráfico de Evolução:** Gráfico de barras empilhadas mostrando contagens de cartões para cada estado ao longo do tempo
- **Períodos de Tempo:** 1 mês, 3 meses, 1 ano ou vida útil do deck
- **Agregação de Dados:** Por dia, semana ou mês com datas absolutas (ex: "24 de out")

#### **Integração com Tela Principal** *(NOVO!)*
- **Tela de Visão Geral:** Gráfico exibido na visão geral do deck
- **Navegador de Decks:** Gráfico exibido na tela do navegador de decks
- **Personalizável:** Período, nível de agregação e altura configuráveis

#### **Estados dos Cartões e Cores**
- **Azul (Retido):** Cartões com intervalos > 84 dias
- **Verde Escuro (Maduro):** Cartões com intervalos de 21-84 dias
- **Verde Claro (Jovem):** Cartões com intervalos de 7-21 dias
- **Laranja (Aprendendo):** Cartões com intervalos ≤ 7 dias ou em fases de aprendizado

#### **Funcionalidades Interativas**
- **Tooltips:** Passe o mouse para ver contagens detalhadas e totais
- **Personalização:** Mostrar/ocultar estados específicos via configuração
- **Exibição Flexível:** Escolha posição do gráfico e formato de data

### Benefícios

- **Acompanhe o Progresso:** Monitore como as distribuições de cartões mudam ao longo do tempo
- **Identifique Padrões:** Entenda a progressão do aprendizado e gargalos
- **Múltiplas Visualizações:** Acesse gráficos da tela de estatísticas e interface principal

---

## **Configuration**

<p align="center">
  <img src="https://i.ibb.co/ymZ6pbBr/image.png" alt="Configuration">
</p>

---

## **License and Contact**

- **Copyright(C)** [Carlos Duarte]
- Licensed under [GNU AGPL, version 3](http://www.gnu.org/licenses/agpl.html)
- For bugs or suggestions, please open an issue at [https://github.com/cjdduarte/AccumulatedRetentionGraph/issues](https://github.com/cjdduarte/AccumulatedRetentionGraph/issues)

## **Changelog**

- **v1.4 - 2025-06-06 - Main Screen Integration**
    - **NEW:** Added graph display to Anki's main screen (overview and deck browser)
    - **NEW:** Configurable main screen options: period, aggregation, height
    - **NEW:** Individual controls for overview and deck browser display
    - Improved translation system with automatic language detection
    - Enhanced configuration documentation
    - Default main screen integration enabled

- **v1.3 - 2025-06-05 - UI/UX Improvements & Absolute Dates**
    - The graph's x-axis and tooltips now display absolute dates (e.g., "Oct 24") by default for better readability
    - Added `use_absolute_dates` configuration option (default: `true`)
    - Standardized the "Today" label across all graph views
    - Improved tooltip and legend rendering consistency
    - Adjusted title and subtitle spacing for compact layout
    - Fixed container border display issues in deck overview screen

- **v1.2 - 2025-06-04 - Automatic Translation System**
    - Complete overhaul of translation system with automatic language detection
    - Dynamic language support extraction from `config.json`
    - Added full Spanish support by default
    - More robust system using native Anki functions

- **v1.1 - 2025-05-28 - Exclude Deleted Cards**
    - Added `exclude_deleted_cards` option (default: true)

- **v1.0 - 2025-05-27 - Initial Release**
    - Stacked bar graph of card states over time
    - Data aggregation based on statistics period
    - Customizable card state visibility
    - Tooltip display with detailed counts
    - Basic internationalization (English, Portuguese)
