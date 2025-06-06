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
            return supported
    except Exception as e:
        pass
    
    # Fallback para lista mínima
    return [DEFAULT_LANG]

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
    except Exception as e:
        pass

    if raw_anki_lang:
        # Match exato
        if raw_anki_lang in supported_languages:
            return raw_anki_lang
        # Match por prefixo (ex: "pt" de "pt_BR")
        lang_prefix = raw_anki_lang[:2]
        if lang_prefix in supported_languages:
            return lang_prefix

    # 2. Tentar idioma do sistema
    raw_sys_lang = None
    try:
        raw_sys_lang = QLocale().name()  # Formato "en_US", "pt_BR"
    except Exception as e:
        pass

    if raw_sys_lang:
        # Match exato
        if raw_sys_lang in supported_languages:
            return raw_sys_lang
        # Match por prefixo
        sys_lang_prefix = raw_sys_lang[:2]
        if sys_lang_prefix in supported_languages:
            return sys_lang_prefix

    # 3. Fallback para idioma padrão
    return DEFAULT_LANG

def tr(key: str, **kwargs: Any) -> str:
    """Traduz uma chave para o idioma atual usando os mapas do config.json."""
    lang_code = get_language_code()
    
    config = mw.addonManager.getConfig(__package__)
    if not config:
        return key

    translation_maps = config.get("translation_maps")
    if not translation_maps or not isinstance(translation_maps, dict):
        return key

    # Log dos termos encontrados na primeira chamada
    if not hasattr(tr, "_logged_terms"):
        tr._logged_terms = True

    default_lang_map = translation_maps.get(DEFAULT_LANG, {})
    current_lang_map = translation_maps.get(lang_code, default_lang_map)
    
    text_template = current_lang_map.get(key)
    found_in_current = text_template is not None

    if not found_in_current and lang_code != DEFAULT_LANG:
        text_template = default_lang_map.get(key)
    
    if text_template is None:
        return key
    
    try:
        return text_template.format(**kwargs) if kwargs else text_template
    except KeyError as e:
        return key
    except Exception as e:
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