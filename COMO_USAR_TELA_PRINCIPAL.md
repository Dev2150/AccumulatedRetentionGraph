# Como Usar o Gráfico na Tela Principal

## 🚀 Ativação Rápida

### 1. Modificar Configuração
Abra o arquivo `config.json` do addon e altere:

```json
{
    "enable_main_screen": true
}
```

### 2. Reiniciar o Anki
Feche e reabra o Anki para carregar as mudanças.

### 3. Testar
- Vá para a **visão geral de um deck** (clique em um deck)
- Ou vá para o **navegador de decks** (tela principal)
- O gráfico deve aparecer na parte inferior da tela

## ⚙️ Configurações Disponíveis

### Configurações Básicas
```json
{
    "enable_main_screen": true,           // Habilitar funcionalidade
    "main_screen_period": "3m",           // Período: "1m", "3m", "1y", "deck_life"
    "main_screen_height": 250,            // Altura em pixels
    "show_in_overview": true,             // Mostrar na visão geral do deck
    "show_in_deck_browser": true,         // Mostrar no navegador de decks
    "show_no_data_message": false         // Mostrar msg quando sem dados
}
```

### Períodos Disponíveis
- **"1m"** - Último mês (agregação diária)
- **"3m"** - Últimos 3 meses (agregação semanal) - **Recomendado**
- **"1y"** - Último ano (agregação mensal)
- **"deck_life"** - Vida inteira do deck/coleção (agregação mensal)

### Controle de Visibilidade das Séries
```json
{
    "hide_learning": false,    // Ocultar série "Aprendendo"
    "hide_young": false,       // Ocultar série "Jovens"
    "hide_mature": false,      // Ocultar série "Maduros"
    "hide_retained": false     // Ocultar série "Retidos"
}
```

## 🎯 Onde o Gráfico Aparece

### Visão Geral do Deck
- Clique em qualquer deck na tela principal
- O gráfico mostra dados **apenas desse deck** (incluindo subdecks)

### Navegador de Decks (Tela Principal)
- Tela inicial do Anki com lista de decks
- O gráfico mostra dados de **toda a coleção**

## 🛠️ Solução de Problemas

### Gráfico não aparece?
1. ✅ Verificar se `"enable_main_screen": true`
2. ✅ Reiniciar o Anki após mudanças na config
3. ✅ Verificar se há dados de revisão suficientes
4. ✅ Verificar console do Anki para erros

### Gráfico vazio?
- Experimente um período menor (ex: "1m" ao invés de "deck_life")
- Verifique se o deck selecionado tem revisões
- Configure `"show_no_data_message": true` para ver mensagens informativas

### Performance lenta?
- Use período "3m" ao invés de "deck_life"
- Considere `"exclude_deleted_cards": true` (padrão)
- Diminua `main_screen_height` se necessário

## 📊 Interpretação do Gráfico

### Cores e Significados
- 🔵 **Azul (Retidos)**: Cartões com intervalos > 84 dias
- 🟢 **Verde Escuro (Maduros)**: Intervalos > 21 dias e ≤ 84 dias  
- 🟢 **Verde Claro (Jovens)**: Intervalos > 7 dias e ≤ 21 dias
- 🟠 **Laranja (Aprendendo)**: Intervalos ≤ 7 dias ou em aprendizado

### Eixos
- **X**: Tempo (dias/semanas/meses dependendo do período)
- **Y**: Número de cartões
- **Tooltip**: Passe o mouse sobre as barras para detalhes

## 🔄 Configuração Recomendada

Para a maioria dos usuários:

```json
{
    "enable_main_screen": true,
    "main_screen_period": "3m",
    "main_screen_height": 250,
    "show_in_overview": true,
    "show_in_deck_browser": true,
    "show_no_data_message": false,
    "hide_learning": false,
    "hide_young": false,
    "hide_mature": false,
    "hide_retained": false
}
```

Esta configuração oferece boa performance e visualização útil para acompanhar o progresso dos estudos.

## 💡 Dicas Avançadas

1. **Performance**: Para coleções grandes, use períodos menores ("1m" ou "3m")
2. **Foco**: Oculte séries que não interessam usando `hide_*`
3. **Altura**: Ajuste `main_screen_height` conforme sua preferência visual
4. **Debug**: Ative `show_no_data_message` temporariamente para diagnosticar problemas 