import json
from pathlib import Path

_LOCALES_DIR = Path(__file__).parent / "locales"
_DEFAULT_LANG = "en"
_SUPPORTED_LANGS = {"en", "zh", "hi", "es", "fr", "ar", "bn", "ru", "pt", "id", "de", "ja", "pa", "jv", "ko", "uk"}

_translations: dict[str, dict] = {}


def _load_translations() -> None:
    for lang in _SUPPORTED_LANGS:
        path = _LOCALES_DIR / f"{lang}.json"
        with open(path, encoding="utf-8") as f:
            _translations[lang] = json.load(f)


_load_translations()


def normalize_language_code(lang_code: str | None) -> str:
    """Normalize a Telegram language_code to one of our supported language codes.

    Telegram may send codes like "zh-hans", "pt-br", "en-us", etc.
    We extract the primary subtag (before the first hyphen) and check whether
    it is one of our supported languages. Falls back to English if not.
    """
    if not lang_code:
        return _DEFAULT_LANG
    primary = lang_code.split("-")[0].lower()
    return primary if primary in _SUPPORTED_LANGS else _DEFAULT_LANG


def get_text(key: str, lang: str | None = None) -> str:
    lang = lang if lang in _SUPPORTED_LANGS else _DEFAULT_LANG
    parts = key.split(".")
    node = _translations.get(lang, _translations[_DEFAULT_LANG])
    for part in parts:
        if isinstance(node, dict):
            node = node.get(part, "")
        else:
            return key
    if not node:
        # fallback to default language
        node = _translations[_DEFAULT_LANG]
        for part in parts:
            if isinstance(node, dict):
                node = node.get(part, key)
            else:
                return key
    return str(node) if node else key
