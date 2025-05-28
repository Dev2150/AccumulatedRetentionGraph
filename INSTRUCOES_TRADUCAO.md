# Guia Universal para Implementação de Sistema de Tradução em Addons Anki

Este guia descreve um método para implementar um sistema de tradução multilíngue em addons Anki, movendo strings traduzíveis para o arquivo `config.json` do addon e utilizando um módulo `translations.py` para gerenciar a lógica de tradução.

## Estrutura de Arquivos e Componentes Chave:

1.  **`config.json` (na raiz do addon):**
    *   Armazena todas as traduções.
    *   Contém uma chave principal `"translation_maps"`.
    *   Dentro de `"translation_maps"`, cada idioma suportado tem seu próprio objeto-mapa (ex: `"en"`, `"pt_BR"`, `"es"`).
    *   Cada mapa de idioma contém pares de `chave_de_traducao: "Texto traduzido"`.

2.  **`translations.py` (na raiz do addon):**
    *   Centraliza a lógica de detecção de idioma e busca de traduções.
    *   Principais componentes:
        *   `SUPPORTED_LANGUAGES = ["en", "pt_BR", ...]` (lista de códigos de idioma).
        *   `DEFAULT_LANG = "en"` (idioma padrão).
        *   `get_language_code() -> str`: Detecta o idioma ativo (Anki, sistema, fallback para `DEFAULT_LANG`).
        *   `tr(key: str, **kwargs: Any) -> str`: Função principal para buscar e formatar traduções.

3.  **Arquivos `.py` do Addon (ex: `__init__.py`, outros módulos):**
    *   Importam a função `tr` de `translations.py`.
    *   Usam `tr("chave_de_traducao")` para exibir texto ao usuário.

## Passos Detalhados para Implementação:

**1. Preparar o Arquivo `config.json`**

*   Abra o arquivo `config.json` do seu addon.
*   Adicione a seguinte estrutura (ou mescle com configurações existentes):

    ```json
    {
        // ... outras configurações existentes do addon ...
        "translation_maps": {
            "en": {
                "greeting_key": "Hello",
                "farewell_key": "Goodbye, {user_name}!"
                // ... outras chaves e traduções em inglês ...
            },
            "pt_BR": {
                "greeting_key": "Olá",
                "farewell_key": "Adeus, {user_name}!"
                // ... outras chaves e traduções em português ...
            }
            // ... Adicione outros objetos de idioma conforme necessário ...
        }
    }
    ```

*   **Identifique e Mova Strings:**
    *   Percorra o código Python do seu addon e identifique todas as strings literais que são exibidas ao usuário (rótulos de botões, mensagens, títulos de gráficos, etc.).
    *   Para cada string, crie uma `chave_de_traducao` única (ex: `my_addon_button_label`, `graph_title_main`).
    *   Adicione essa chave e sua tradução correspondente a cada mapa de idioma dentro de `translation_maps` no `config.json`.
        *   *Dica:* Use placeholders como `{user_name}` para strings que precisam de formatação dinâmica.

**2. Criar/Atualizar o Arquivo `translations.py`**

*   Crie um arquivo chamado `translations.py` na raiz do seu addon, com o seguinte conteúdo base:

    ```python
    from typing import Any
    from aqt.qt import QLocale
    from aqt import mw # Necessário para getConfig e preferências de idioma do Anki

    # --- Configuração Específica do Addon ---
    ADDON_ID = "__NAME_OF_YOUR_ADDON_FOLDER__" # IMPORTANTE: Substitua pelo nome da pasta do seu addon
    # -----------------------------------------

    SUPPORTED_LANGUAGES = ["en", "pt_BR"] # Adicione todos os códigos de idioma que você suporta
    DEFAULT_LANG = "en" # Idioma padrão se a detecção falhar ou o idioma não for suportado

    def get_language_code() -> str:
        """
        Determina o código de idioma a ser usado para tradução.
        Prioridade:
        1. Idioma configurado no Anki (match exato ou prefixo de 2 letras).
        2. Idioma do sistema operacional (match exato ou prefixo de 2 letras).
        3. DEFAULT_LANG.
        """
        raw_anki_lang = None
        try:
            # Tenta obter o idioma padrão do perfil Anki (disponível quando um perfil está carregado)
            if mw and mw.pm and mw.pm.meta:
                raw_anki_lang = mw.pm.meta.get('defaultLang')
        except AttributeError:
            # mw, mw.pm, ou mw.pm.meta podem não estar disponíveis em todos os contextos (ex: inicialização precoce)
            pass
        except Exception as e:
            # print(f"[{ADDON_ID}] Error accessing Anki language settings: {e}")
            pass

        if raw_anki_lang:
            if raw_anki_lang in SUPPORTED_LANGUAGES:
                return raw_anki_lang
            lang_prefix = raw_anki_lang[:2]
            if lang_prefix in SUPPORTED_LANGUAGES:
                return lang_prefix

        raw_sys_lang = None
        try:
            raw_sys_lang = QLocale().name()  # Formato como "en_US", "pt_BR"
        except Exception:
            # print(f"[{ADDON_ID}] Error accessing system language: {e}")
            pass # QLocale pode não estar disponível ou falhar

        if raw_sys_lang:
            if raw_sys_lang in SUPPORTED_LANGUAGES:
                return raw_sys_lang
            sys_lang_prefix = raw_sys_lang[:2]
            if sys_lang_prefix in SUPPORTED_LANGUAGES:
                return sys_lang_prefix
                
        return DEFAULT_LANG

    def tr(key: str, **kwargs: Any) -> str:
        """
        Busca uma string de tradução do config.json do addon.
        - `key`: A chave da string a ser traduzida (ex: "greeting_key").
        - `**kwargs`: Argumentos nomeados para formatar a string (ex: nome="Usuário").
        Retorna a string traduzida e formatada, ou a própria chave se não encontrada.
        """
        lang_code = get_language_code()
        
        config = mw.addonManager.getConfig(ADDON_ID)
        if not config:
            # print(f"[{ADDON_ID}] Translation Error: Could not load addon configuration for ADDON_ID: '{ADDON_ID}'.")
            return key

        translation_maps = config.get("translation_maps")
        if not translation_maps or not isinstance(translation_maps, dict):
            # print(f"[{ADDON_ID}] Translation Error: 'translation_maps' not found or not a dict in config.json for ADDON_ID: '{ADDON_ID}'.")
            return key

        # Tenta obter o mapa do idioma atual, senão usa o mapa do idioma padrão
        lang_map = translation_maps.get(lang_code, translation_maps.get(DEFAULT_LANG, {}))
        
        text_template = lang_map.get(key)

        # Se não encontrou no idioma atual/padrão, e o idioma atual NÃO É o padrão, tenta o padrão explicitamente
        if text_template is None and lang_code != DEFAULT_LANG:
            default_map = translation_maps.get(DEFAULT_LANG, {})
            text_template = default_map.get(key)
        
        if text_template is None:
            # print(f"[{ADDON_ID}] Translation Warning: Key '{key}' not found for lang '{lang_code}' (nor in default '{DEFAULT_LANG}'). Displaying key name for ADDON_ID: '{ADDON_ID}'.")
            return key 
        
        try:
            return text_template.format(**kwargs) if kwargs else text_template
        except KeyError as e:
            # print(f"[{ADDON_ID}] Translation Formatting Error for key '{key}' in lang '{lang_code}': {e}. Template: '{text_template}' for ADDON_ID: '{ADDON_ID}'")
            return key # Retorna a chave para indicar um problema de formatação
        except Exception as e:
            # print(f"[{ADDON_ID}] Unexpected error during translation of key '{key}' for ADDON_ID: '{ADDON_ID}': {e}")
            return key
    ```

*   **Importante:**
    *   **Atualize `ADDON_ID`**: Substitua ` "__NAME_OF_YOUR_ADDON_FOLDER__" ` pelo nome exato da pasta raiz do seu addon (este é o ID que o Anki usa para `mw.addonManager.getConfig()`).
    *   **Atualize `SUPPORTED_LANGUAGES`**: Liste todos os códigos de idioma para os quais você forneceu traduções no `config.json`.
    *   **Atualize `DEFAULT_LANG`**: Defina seu idioma padrão preferido.

**3. Modificar Arquivos Python do Addon para Usar Traduções**

*   **Importar `tr`:** Em cada arquivo `.py` que precisa exibir texto traduzível, adicione a importação:
    ```python
    from .translations import tr 
    # Ou, se estiver em subpastas, ajuste o caminho relativo:
    # from ..translations import tr 
    ```

*   **Substituir Strings Literais:**
    *   Encontre todas as strings literais que você moveu para o `config.json`.
    *   Substitua-as por chamadas à função `tr`, usando a chave de tradução correspondente.

    *   **Exemplo:**
        *   Antigo: `my_label.setText("Hello, World!")`
        *   Novo: `my_label.setText(tr("hello_world_key"))`

        *   Antigo (com formatação): `message = f"Welcome, {user_name}."`
        *   Novo: `message = tr("welcome_user_key", user_name=user_name)`

*   **Strings em JavaScript (ex: para gráficos Flot):**
    *   Se você tem strings que precisam ser passadas para código JavaScript (como em tooltips de gráficos ou formatadores de eixos), traduza-as no Python antes de injetá-las no bloco JavaScript.

    *   **Exemplo (Python):**
        ```python
        from .translations import tr
        # ...
        tr_today_label = tr("js_today_label")
        tr_period_label = tr("js_period_label")

        tooltip_js_code = f"""
        function(...) {{
            // ...
            var todayText = '{tr_today_label}';
            var periodText = '{tr_period_label}';
            // ... usa todayText e periodText no JS ...
        }}
        """
        # ...
        ```
        No `config.json`, você teria:
        ```json
        "en": {
            "js_today_label": "Today",
            "js_period_label": "Period: "
            // ...
        },
        "pt_BR": {
            "js_today_label": "Hoje",
            "js_period_label": "Período: "
            // ...
        }
        ```

**4. Testar Completamente**

*   Após implementar as mudanças, teste seu addon:
    *   Mude o idioma do Anki para cada um dos `SUPPORTED_LANGUAGES` e verifique se todas as strings aparecem corretamente traduzidas.
    *   Verifique o idioma padrão.
    *   Teste com um idioma não suportado para garantir que ele recorra ao `DEFAULT_LANG`.
    *   Verifique o console do Anki (Ferramentas > Add-ons > Selecione seu addon > Verificar Arquivos > ... > Debug Console (se disponível via Anki Debug Tools) ou procure por logs se você descomentou os `print`s em `translations.py`) por quaisquer mensagens de erro ou aviso de tradução (chaves não encontradas, erros de formatação).

## Considerações Adicionais:

*   **Nomes de Chave:** Escolha nomes de chave descritivos e consistentes.
*   **Contexto `mw`:** A função `get_language_code` e `tr` dependem de `mw` (a janela principal do Anki) para acessar as configurações do gerenciador de addons e as preferências de idioma. Isso geralmente está disponível quando a UI do addon é carregada. Se você precisar de traduções em um contexto onde `mw` não está disponível (o que é raro para strings voltadas para o usuário), você pode precisar de uma estratégia de fallback mais simples ou carregar as traduções de uma maneira diferente para esse contexto específico.
*   **Atualização Dinâmica de Idioma:** Se o usuário mudar o idioma do Anki *durante uma sessão* e seu addon já estiver carregado, as strings traduzidas podem não atualizar imediatamente, pois `lang_code` é tipicamente determinado quando `tr` é chamado. Para a maioria dos addons, isso não é um grande problema, pois os usuários geralmente reiniciam o Anki após mudar o idioma. Uma atualização mais dinâmica exigiria hooks ou recarregar partes da UI do addon.
*   **Manutenção:** Mantenha seu `config.json` e `translations.py` atualizados à medida que você adiciona ou modifica strings traduzíveis no seu addon.

Este guia fornece uma base sólida para internacionalizar seu addon Anki. Lembre-se de substituir `ADDON_ID` e adaptar `SUPPORTED_LANGUAGES` e `DEFAULT_LANG` às suas necessidades. 