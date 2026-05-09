"""PyInstaller 런타임 훅 — 번들 앱에서 Qt 플러그인 경로와 메타데이터 경로를 설정한다."""
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
    # dist-info는 Contents/Resources/ 에 배치됨 (codesign 호환)
    _resources = os.path.join(os.path.dirname(_base), "Resources")
    if _resources not in sys.path:
        sys.path.insert(0, _resources)
