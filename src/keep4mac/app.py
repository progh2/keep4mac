import logging
import sys

from PyQt6.QtWidgets import QApplication

from keep4mac.ui.tray_icon import TrayIcon

logger = logging.getLogger(__name__)


def _hide_from_dock():
    """macOS에서 Dock 아이콘을 숨기고 메뉴바 전용 앱으로 설정."""
    try:
        import AppKit
        AppKit.NSApp.setActivationPolicy_(
            AppKit.NSApplicationActivationPolicyAccessory
        )
    except Exception as e:
        logger.debug("Dock 숨김 처리 실패 (개발 환경 무시): %s", e)


class Keep4MacApp:
    def __init__(self, qt_app: QApplication):
        self.qt_app = qt_app
        self._tray: TrayIcon | None = None

    def start(self):
        _hide_from_dock()

        self._tray = TrayIcon(self.qt_app)
        self._tray.show()

        logger.info("keep4mac 시작됨")
