import json
import os
from pathlib import Path

_LOCALES_DIR = Path(__file__).parent / "locales"
_DEFAULT_LANG = "en"
_SUPPORTED_LANGS = {"en", "uk"}
_translations: dict[str, dict] = {}


def _load_translations() -> None:
    for lang in _SUPPORTED_LANGS:
        path = _LOCALES_DIR / f"{lang}.json"
        with open(path, encoding="utf-8") as f:
            _translations[lang] = json.load(f)


_load_translations()


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
