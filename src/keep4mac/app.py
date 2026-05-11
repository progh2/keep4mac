import logging
import sys

from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class Keep4MacApp:
    def __init__(self, qt_app: QApplication):
        self.qt_app = qt_app

    def start(self):
        if sys.platform == "darwin":
            self._start_macos()
        else:
            self._start_windows()

    def _start_macos(self):
        from keep4mac.ui.tray_icon import TrayApp
        TrayApp(self.qt_app).run()   # rumps NSRunLoop 블로킹

    def _start_windows(self):
        from keep4mac.api.keep_client import KeepClient
        from keep4mac.ui.panel import MainPanel
        from keep4mac.ui.tray_win import WindowsTray

        client = KeepClient()
        if client.resume():
            logger.info("자동 로그인 성공")
            client.load_disk_cache()

        panel = MainPanel(client, quit_callback=self.qt_app.quit)
        tray = WindowsTray(self.qt_app, panel, client)
        tray.start()

        sys.exit(self.qt_app.exec())
