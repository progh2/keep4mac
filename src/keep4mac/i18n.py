"""gettext 기반 다국어 지원 모듈."""
import gettext as _gettext
import locale
import sys
from pathlib import Path

_translation: _gettext.NullTranslations | None = None


def _localedir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "i18n"
    return Path(__file__).parents[2] / "i18n"


def setup() -> None:
    """앱 시작 시 한 번 호출. 시스템 언어를 감지해 번역을 설치한다."""
    global _translation
    lang = (locale.getdefaultlocale()[0] or "en_US").split("_")[0]
    try:
        _translation = _gettext.translation(
            "keep4mac",
            localedir=str(_localedir()),
            languages=[lang, "en"],
        )
    except FileNotFoundError:
        _translation = _gettext.NullTranslations()


def gettext(s: str) -> str:
    if _translation is None:
        return s
    return _translation.gettext(s)


# 각 모듈에서 `from keep4mac.i18n import gettext as _` 로 임포트
