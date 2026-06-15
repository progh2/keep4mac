"""gettext 기반 다국어 지원 모듈."""
import gettext as _gettext
import json
import locale
import os
import sys
from pathlib import Path

_translation: _gettext.NullTranslations | None = None


def _get_settings_path() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "keeptray" / "settings.json"
    return Path.home() / ".config" / "keeptray" / "settings.json"


_SETTINGS_PATH = _get_settings_path()

SUPPORTED_LANGS: dict[str, str] = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
}


def _localedir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "i18n"
    return Path(__file__).parents[2] / "i18n"


def _load_settings() -> dict:
    try:
        return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_settings(data: dict) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def current_lang() -> str:
    """현재 적용된 언어 코드 반환."""
    settings = _load_settings()
    if "lang" in settings:
        return settings["lang"]
    return (locale.getdefaultlocale()[0] or "en_US").split("_")[0]


def save_lang(lang: str) -> None:
    """선택한 언어를 설정 파일에 저장."""
    settings = _load_settings()
    settings["lang"] = lang
    _save_settings(settings)


def setup() -> None:
    """앱 시작 시 한 번 호출. 설정 파일 → 시스템 언어 순으로 감지해 번역을 설치한다."""
    global _translation
    lang = current_lang()
    try:
        _translation = _gettext.translation(
            "keeptray",
            localedir=str(_localedir()),
            languages=[lang, "en"],
        )
    except FileNotFoundError:
        _translation = _gettext.NullTranslations()


def gettext(s: str) -> str:
    if _translation is None:
        return s
    return _translation.gettext(s)


# 각 모듈에서 `from keeptray.i18n import gettext as _` 로 임포트
