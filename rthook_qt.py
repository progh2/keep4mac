"""PyInstaller 런타임 훅 — 번들 앱에서 Qt 플러그인 경로를 설정한다."""
import os
import sys

if getattr(sys, "frozen", False):
    _base = sys._MEIPASS
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(
        _base, "PyQt6", "Qt6", "plugins", "platforms"
    )
    os.environ["QT_PLUGIN_PATH"] = os.path.join(
        _base, "PyQt6", "Qt6", "plugins"
    )
