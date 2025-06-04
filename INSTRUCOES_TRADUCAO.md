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
        *   `DEFAULT_LANG = "en"` (idioma padrão).
        *   `get_supported_languages() -> list`: Extrai dinamicamente os idiomas suportados do `config.json`.
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
    from aqt import mw

    DEFAULT_LANG = "en"

    def get_supported_languages() -> list:
        """Extrai dinamicamente os idiomas suportados do config.json."""
        try:
            config = mw.addonManager.getConfig(__package__)
            if config and "translation_maps" in config:
                supported = list(config["translation_maps"].keys())
                print(f"[Addon: {__package__}] Idiomas suportados encontrados no config: {supported}")
                return supported
        except Exception as e:
            print(f"[Addon: {__package__}] Erro ao extrair idiomas do config: {e}")
        
        # Fallback para lista mínima
        fallback = [DEFAULT_LANG]
        print(f"[Addon: {__package__}] Usando fallback de idiomas: {fallback}")
        return fallback

    def get_language_code() -> str:
        """
        Detecta o idioma atual usando funções nativas do Anki.
        Prioridade: Anki -> Sistema -> DEFAULT_LANG
        """
        supported_languages = get_supported_languages()
        
        # 1. Tentar idioma do Anki primeiro
        raw_anki_lang = None
        try:
            if mw and mw.pm and mw.pm.meta:
                raw_anki_lang = mw.pm.meta.get('defaultLang')
                print(f"[Addon: {__package__}] Idioma do Anki detectado: {raw_anki_lang}")
        except Exception as e:
            print(f"[Addon: {__package__}] Erro ao acessar idioma do Anki: {e}")

        if raw_anki_lang:
            # Match exato
            if raw_anki_lang in supported_languages:
                print(f"[Addon: {__package__}] Usando idioma do Anki (match exato): {raw_anki_lang}")
                return raw_anki_lang
            # Match por prefixo (ex: "pt" de "pt_BR")
            lang_prefix = raw_anki_lang[:2]
            if lang_prefix in supported_languages:
                print(f"[Addon: {__package__}] Usando idioma do Anki (match prefixo): {lang_prefix}")
                return lang_prefix

        # 2. Tentar idioma do sistema
        raw_sys_lang = None
        try:
            raw_sys_lang = QLocale().name()  # Formato "en_US", "pt_BR"
            print(f"[Addon: {__package__}] Idioma do sistema detectado: {raw_sys_lang}")
        except Exception as e:
            print(f"[Addon: {__package__}] Erro ao acessar idioma do sistema: {e}")

        if raw_sys_lang:
            # Match exato
            if raw_sys_lang in supported_languages:
                print(f"[Addon: {__package__}] Usando idioma do sistema (match exato): {raw_sys_lang}")
                return raw_sys_lang
            # Match por prefixo
            sys_lang_prefix = raw_sys_lang[:2]
            if sys_lang_prefix in supported_languages:
                print(f"[Addon: {__package__}] Usando idioma do sistema (match prefixo): {sys_lang_prefix}")
                return sys_lang_prefix

        # 3. Fallback para idioma padrão
        print(f"[Addon: {__package__}] Usando idioma padrão (fallback): {DEFAULT_LANG}")
        return DEFAULT_LANG

    def tr(key: str, **kwargs: Any) -> str:
        """Traduz uma chave para o idioma atual usando os mapas do config.json."""
        lang_code = get_language_code()
        
        config = mw.addonManager.getConfig(__package__)
        if not config:
            print(f"[Addon: {__package__}] Erro de tradução: Não foi possível carregar configuração do addon.")
            return key

        translation_maps = config.get("translation_maps")
        if not translation_maps or not isinstance(translation_maps, dict):
            print(f"[Addon: {__package__}] Erro de tradução: 'translation_maps' não encontrado ou não é um dict no config.json.")
            return key

        # Log dos termos encontrados na primeira chamada
        if not hasattr(tr, "_logged_terms"):
            print(f"[Addon: {__package__}] Termos de tradução encontrados:")
            for lang, terms in translation_maps.items():
                if isinstance(terms, dict):
                    print(f"  {lang}: {list(terms.keys())}")
            tr._logged_terms = True

        default_lang_map = translation_maps.get(DEFAULT_LANG, {})
        current_lang_map = translation_maps.get(lang_code, default_lang_map)
        
        text_template = current_lang_map.get(key)
        found_in_current = text_template is not None

        if not found_in_current and lang_code != DEFAULT_LANG:
            text_template = default_lang_map.get(key)
        
        if text_template is None:
            print(f"[Addon: {__package__}] Aviso de tradução: Chave '{key}' não encontrada para idioma '{lang_code}' (nem no padrão '{DEFAULT_LANG}').")
            return key
        
        try:
            return text_template.format(**kwargs) if kwargs else text_template
        except KeyError as e:
            print(f"[Addon: {__package__}] Erro de formatação na tradução da chave '{key}' em '{lang_code}': {e}. Template: '{text_template}'")
            return key
        except Exception as e:
            print(f"[Addon: {__package__}] Erro inesperado na tradução da chave '{key}': {e}")
            return key
    ```

*   **Importante:**
    *   **Sistema Automático**: O sistema agora extrai automaticamente os idiomas suportados do `config.json`, não sendo necessário manter uma lista hard-coded.
    *   **Logs Informativos**: O sistema produz logs detalhados mostrando idiomas detectados, termos encontrados e decisões de tradução.
    *   **Funções Nativas do Anki**: Usa `mw.pm.meta.get('defaultLang')` e `QLocale().name()` para detectar idiomas.

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
    *   Mude o idioma do Anki para cada um dos idiomas suportados e verifique se todas as strings aparecem corretamente traduzidas.
    *   Verifique o idioma padrão.
    *   Teste com um idioma não suportado para garantir que ele recorra ao `DEFAULT_LANG`.
    *   Verifique o console do Anki (Ferramentas > Add-ons > Debug Console) pelos logs informativos do sistema de tradução, que mostrarão:
        *   Idiomas suportados encontrados
        *   Idioma detectado do Anki/sistema
        *   Idioma escolhido para uso
        *   Termos de tradução disponíveis
        *   Avisos de chaves não encontradas

## Considerações Adicionais:

*   **Nomes de Chave:** Escolha nomes de chave descritivos e consistentes.
*   **Logs de Debug:** Os logs são úteis durante desenvolvimento. Você pode comentar ou remover os `print`s após a implementação estar estável.
*   **Detecção Automática:** O sistema detecta automaticamente os idiomas disponíveis no `config.json`, facilitando adição de novos idiomas.
*   **Contexto `mw`:** As funções dependem de `mw` (janela principal do Anki) para acessar configurações. Isso está disponível quando a UI do addon é carregada.
*   **Atualização Dinâmica:** Se o usuário mudar o idioma do Anki durante uma sessão, as traduções podem não atualizar imediatamente. Usuários geralmente reiniciam o Anki após mudanças de idioma.
*   **Manutenção:** Mantenha seu `config.json` atualizado à medida que adiciona novas strings traduzíveis.

## Recursos Avançados:

*   **Fallback Inteligente:** Se uma chave não existe no idioma atual, o sistema automaticamente tenta o idioma padrão.
*   **Match por Prefixo:** Se "pt_BR" não é suportado mas "pt" é, o sistema usa "pt" automaticamente.
*   **Formatação Dinâmica:** Suporte completo a placeholders para strings com variáveis.

Este guia fornece uma base sólida e moderna para internacionalizar seu addon Anki com detecção automática de idiomas e logs informativos para facilitar debug e manutenção. 