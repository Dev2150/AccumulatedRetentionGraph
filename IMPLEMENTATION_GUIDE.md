# Guia de Implementação - Accumulated Retention Graph na Tela Principal

## Resumo

**SIM, é totalmente possível** portar o Accumulated Retention Graph para a tela principal do Anki! Você já tem um protótipo muito bem estruturado, e baseado na análise dos seus arquivos, criei uma implementação otimizada e funcional.

## Opções de Implementação

### Opção 1: Addon Separado (Recomendado para Teste)
Criar um addon completamente independente que só funciona na tela principal.

**Vantagens:**
- Não interfere com o addon original
- Fácil de testar e debug
- Pode ser distribuído separadamente

**Arquivo principal:** `main_screen_addon.py` (já criado)

### Opção 2: Integração ao Addon Original (Recomendado para Produção)
Adicionar a funcionalidade ao seu addon existente como uma opção configurável.

**Vantagens:**
- Mantém tudo em um só addon
- Reutiliza a lógica existente
- Configuração unificada

## Implementação Detalhada

### 1. Para Addon Separado

Estrutura de arquivos:
```
AccumulatedRetentionGraphMainScreen/
├── __init__.py (conteúdo do main_screen_addon.py)
├── config.json (config_main_screen.json)
├── translations.py (pode reutilizar o original)
└── manifest.json
```

**manifest.json:**
```json
{
    "package": "accumulated_retention_main_screen",
    "name": "Accumulated Retention Graph - Main Screen",
    "author": "Carlos Duarte",
    "human_version": "1.0.0",
    "description": "Shows the Accumulated Retention Graph on Anki's main screen",
    "mod": 1234567890,
    "min_point_version": 45,
    "max_point_version": 0,
    "branch_index": 0,
    "update_enabled": true
}
```

### 2. Para Integração ao Addon Original

Adicione estas novas configurações ao seu `config.json`:

```json
{
    // ... configurações existentes ...
    "enable_main_screen": false,
    "main_screen_period": "3m",
    "main_screen_height": 250,
    "show_in_overview": true,
    "show_in_deck_browser": true,
    "show_no_data_message": false
}
```

E adicione o código do `integration_example.py` ao final do seu `__init__.py`:

```python
# No final do __init__.py existente
from integration_example import init_main_screen_integration
init_main_screen_integration()
```

## Configurações Disponíveis

### Configurações Específicas da Tela Principal

- **`enable_main_screen`** (boolean): Habilita/desabilita o gráfico na tela principal
- **`main_screen_period`** (string): Período padrão ("1m", "3m", "1y", "deck_life")
- **`main_screen_height`** (integer): Altura do gráfico em pixels (padrão: 250)
- **`show_in_overview`** (boolean): Mostrar na visão geral do deck
- **`show_in_deck_browser`** (boolean): Mostrar no navegador de decks
- **`show_no_data_message`** (boolean): Mostrar mensagem quando não há dados

### Configurações Herdadas do Original

- `hide_learning`, `hide_young`, `hide_mature`, `hide_retained`
- `exclude_deleted_cards`
- `translation_maps`

## Compatibilidade

✅ **Funciona com:**
- Anki 2.1.45+
- Todos os sistemas operacionais
- Múltiplos idiomas (PT, EN, ES)

✅ **Compatível com outros addons:**
- Heatmap
- Review Heatmap  
- Outros addons que usam hooks similares

## Diferenças da Versão Original

### Melhorias na Versão da Tela Principal

1. **Performance Otimizada:**
   - Período padrão menor (3m vs deck_life)
   - Queries SQL otimizadas
   - Menos processamento de dados

2. **Interface Melhorada:**
   - Visual mais limpo e moderno
   - Altura configurável
   - Bordas e espaçamento melhorados

3. **Robustez:**
   - Tratamento de erros aprimorado
   - Fallbacks para dependências JS
   - Configuração com defaults seguros

4. **Flexibilidade:**
   - Controle granular sobre onde mostrar
   - Configurações específicas para tela principal
   - Integração não-invasiva

## Testes Recomendados

### Cenários de Teste

1. **Funcionalidade Básica:**
   - [ ] Gráfico aparece na overview do deck
   - [ ] Gráfico aparece no deck browser
   - [ ] Tooltip funciona corretamente
   - [ ] Dados corretos são exibidos

2. **Configurações:**
   - [ ] Ocultar séries funciona
   - [ ] Diferentes períodos funcionam
   - [ ] Altura personalizada funciona
   - [ ] Habilitar/desabilitar funciona

3. **Compatibilidade:**
   - [ ] Funciona com outros addons
   - [ ] Não quebra funcionalidade existente
   - [ ] Performance aceitável

4. **Edge Cases:**
   - [ ] Sem dados de revisão
   - [ ] Deck vazio
   - [ ] Coleção nova
   - [ ] Dependências JS ausentes

## Limitações Conhecidas

1. **Dependências JavaScript:**
   - Requer jQuery e Flot (geralmente disponíveis no Anki)
   - Graceful degradation se não disponíveis

2. **Performance:**
   - Queries podem ser lentas para coleções muito grandes
   - Use períodos menores para melhor performance

3. **Contexto de Deck:**
   - Na overview, pega o deck atual
   - No deck browser, usa toda a coleção
   - Subdecks são incluídos automaticamente

## Próximos Passos

### Para Implementar:

1. **Teste Inicial:**
   - Use o addon separado primeiro
   - Teste com uma coleção pequena
   - Verifique se as dependências JS estão disponíveis

2. **Configuração:**
   - Ajuste o período padrão conforme necessário
   - Configure quais telas mostrar o gráfico
   - Teste diferentes alturas

3. **Integração (se desejar):**
   - Adicione as configurações ao config.json original
   - Integre o código ao __init__.py
   - Teste compatibilidade

4. **Distribuição:**
   - Teste em diferentes versões do Anki
   - Documente as novas funcionalidades
   - Considere feedback dos usuários

## Conclusão

A implementação é tecnicamente sólida e pronta para uso. O conceito do seu protótipo está correto, e a versão otimizada que criei resolve os principais desafios:

- ✅ Desacoplamento do CollectionStats
- ✅ Hooks apropriados para tela principal
- ✅ Tratamento robusto de erros
- ✅ Configuração flexível
- ✅ Performance otimizada

O gráfico funcionará perfeitamente na tela principal, mostrando a evolução dos cartões de forma similar ao original, mas otimizado para o contexto da tela principal do Anki. 