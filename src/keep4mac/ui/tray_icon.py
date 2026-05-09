import logging
import sys

import rumps
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

from keep4mac.api.keep_client import KeepClient
from keep4mac.ui.panel import MainPanel

logger = logging.getLogger(__name__)

ICON_CHAR = "🗒"


class TrayApp(rumps.App):
    def __init__(self, qt_app: QApplication):
        super().__init__(name="keep4mac", title=ICON_CHAR, quit_button=None)
        self._qt_app = qt_app

        self._client = KeepClient()
        # 저장된 토큰으로 자동 재인증 시도
        if self._client.resume():
            logger.info("자동 로그인 성공")

        self._panel = MainPanel(self._client)

        self.menu = [
            rumps.MenuItem("열기", callback=self._open),
            rumps.MenuItem("동기화", callback=self._sync),
            None,
            rumps.MenuItem("종료", callback=self._quit),
        ]

    @rumps.timer(0.05)
    def _process_qt(self, _):
        QCoreApplication.processEvents()

    def _open(self, _):
        self._panel.show_near_menubar()

    def _sync(self, _):
        if not self._client.is_logged_in:
            rumps.notification("keep4mac", "", "먼저 로그인해주세요.")
            return
        try:
            self._client.sync()
            rumps.notification("keep4mac", "", "동기화 완료!")
        except Exception as e:
            rumps.notification("keep4mac", "동기화 실패", str(e))

    def _quit(self, _):
        self._panel.hide()
        rumps.quit_application()
