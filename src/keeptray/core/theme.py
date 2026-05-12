"""시스템 다크/라이트 모드 감지 및 색상 테마 정의."""
import sys

from keeptray.core import settings as _settings

LIGHT: dict[str, str] = {
    "bg":           "#f5f5f7",
    "surface":      "#ffffff",
    "surface2":     "#f2f2f7",
    "border":       "#d1d1d6",
    "border2":      "#e5e5ea",
    "text":         "#1c1c1e",
    "text2":        "#636366",
    "text3":        "#8e8e93",
    "accent":       "#007AFF",
    "sidebar_bg":   "transparent",
    "scroll_bg":    "#ffffff",
}

DARK: dict[str, str] = {
    "bg":           "#1c1c1e",
    "surface":      "#2c2c2e",
    "surface2":     "#3a3a3c",
    "border":       "#3a3a3c",
    "border2":      "#48484a",
    "text":         "#f5f5f7",
    "text2":        "#aeaeb2",
    "text3":        "#636366",
    "accent":       "#0a84ff",
    "sidebar_bg":   "transparent",
    "scroll_bg":    "#2c2c2e",
}


def _system_is_dark() -> bool:
    if sys.platform == "darwin":
        try:
            from AppKit import NSAppearance, NSApplication
            app = NSApplication.sharedApplication()
            appearance = app.effectiveAppearance()
            name = appearance.bestMatchFromAppearancesWithNames_(
                ["NSAppearanceNameAqua", "NSAppearanceNameDarkAqua"]
            )
            return name == "NSAppearanceNameDarkAqua"
        except Exception:
            pass
    try:
        from PyQt6.QtGui import QGuiApplication, QPalette
        palette = QGuiApplication.palette()
        bg = palette.color(QPalette.ColorRole.Window)
        return bg.lightness() < 128
    except Exception:
        return False


def get_colors() -> dict[str, str]:
    """현재 테마 설정에 따라 색상 딕셔너리를 반환한다."""
    theme = _settings.get_theme()
    if theme == "dark":
        return DARK
    if theme == "light":
        return LIGHT
    return DARK if _system_is_dark() else LIGHT


def is_dark() -> bool:
    return get_colors() is DARK
