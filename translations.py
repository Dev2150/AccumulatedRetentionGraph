from typing import Any # Added for type hinting
from aqt.qt import QLocale
from aqt import mw

# Supported languages
SUPPORTED_LANGUAGES = ["en", "pt_BR"]
DEFAULT_LANG = "en"

def get_language_code() -> str:
    """
    Gets the current Anki language, falling back to system language or default.
    Tries to match exact supported language codes first, then prefixes.
    """
    raw_anki_lang = None
    try:
        raw_anki_lang = mw.pm.meta.get('defaultLang')
    except AttributeError:
        pass # mw or mw.pm not available
    except Exception:
        pass # Other error fetching Anki lang

    if raw_anki_lang:
        # 1. Try exact match with Anki's language setting
        if raw_anki_lang in SUPPORTED_LANGUAGES:
            return raw_anki_lang
        # 2. Try prefix match with Anki's language setting (e.g., "pt" from "pt_BR")
        #    Ensure the prefix itself is a supported code.
        lang_prefix = raw_anki_lang[:2]
        if lang_prefix in SUPPORTED_LANGUAGES:
            return lang_prefix

    raw_sys_lang = None
    try:
        raw_sys_lang = QLocale().name() # Format like "en_US", "pt_BR"
    except Exception:
        pass # Error fetching system lang

    if raw_sys_lang:
        # 3. Try exact match with system language
        if raw_sys_lang in SUPPORTED_LANGUAGES:
            return raw_sys_lang
        # 4. Try prefix match with system language
        sys_lang_prefix = raw_sys_lang[:2]
        if sys_lang_prefix in SUPPORTED_LANGUAGES:
            return sys_lang_prefix
            
    return DEFAULT_LANG # Final fallback

def tr(key: str, **kwargs: Any) -> str:
    """Translates a key into the current language using maps from config.json."""
    lang_code = get_language_code()
    
    # This function uses mw.addonManager.getConfig(__package__) to load the
    # configuration for the current addon. The __package__ variable typically
    # resolves to the addon's root folder name, which Anki uses as the addon ID.
    #
    # For example, if your addon's folder is named "MySuperAddon",
    # __package__ would likely be "MySuperAddon", and Anki's addon manager
    # would use this ID to find the correct config.json file.
    #
    # The core idea is to retrieve the 'translation_maps' from the addon's
    # config.json based on this dynamically determined package name.
    all_config = mw.addonManager.getConfig(__package__)

    if not all_config:
        print(f"[Addon: {__package__}] Translation Error: Could not load addon configuration.")
        return key

    translation_maps = all_config.get("translation_maps")
    if not translation_maps or not isinstance(translation_maps, dict):
        print(f"[Addon: {__package__}] Translation Error: \'translation_maps\' not found or not a dictionary in config.json.")
        return key

    default_lang_map = translation_maps.get(DEFAULT_LANG, {})
    current_lang_map = translation_maps.get(lang_code, default_lang_map)
    
    text_template = current_lang_map.get(key)
    found_in_current = text_template is not None

    if not found_in_current and lang_code != DEFAULT_LANG:
        # Try fallback to DEFAULT_LANG if not already using it and key not in current lang
        text_template = default_lang_map.get(key)
    
    if text_template is None: # Still not found in current or default language map
        print(f"[Addon: {__package__}] Translation Warning: Key \'{key}\' not found for language \'{lang_code}\' (nor in default \'{DEFAULT_LANG}\'). Displaying key name.")
        return key # Return key itself
    
    try:
        return text_template.format(**kwargs) if kwargs else text_template
    except KeyError as e:
        print(f"[Addon: {__package__}] Translation Formatting Error for key \'{key}\' in lang \'{lang_code}\': {e}. Template: \'{text_template}\'")
        return key
    except Exception as e:
        print(f"[Addon: {__package__}] Unexpected error during translation of key \'{key}\': {e}")
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