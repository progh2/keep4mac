import logging
import sys

from PyQt6.QtWidgets import QApplication

from keep4mac.ui.tray_icon import TrayApp

logger = logging.getLogger(__name__)


class Keep4MacApp:
    def __init__(self, qt_app: QApplication):
        self.qt_app = qt_app
        self._tray: TrayApp | None = None

    def start(self):
        self._tray = TrayApp(self.qt_app)
        self._tray.run()   # rumps가 NSRunLoop을 점유 (블로킹)
