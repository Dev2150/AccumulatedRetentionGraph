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

# Add a way to allow dynamic updates if Anki language changes during session
# This is a simplified version. A more robust solution might involve hooks.
def _update_translation_lang_if_needed():
    # This function could be called periodically or on certain events
    # to re-check mw.pm.meta if it\'s available.
    # For now, get_language_code handles fallback if mw isn\'t ready.
    pass

if mw and hasattr(mw, "form") and hasattr(mw.form, "menuCol"):
    # Example: try to refresh lang if some major UI part is available.
    # This is just a conceptual placeholder for a better trigger.
    pass 