import logging
import sys

import rumps
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

from keep4mac.ui.panel import MainPanel

logger = logging.getLogger(__name__)

ICON_CHAR = "🗒"   # 노트 이모지 — 메뉴바에 텍스트로 표시


class TrayApp(rumps.App):
    """rumps 기반 네이티브 macOS 메뉴바 앱."""

    def __init__(self, qt_app: QApplication):
        super().__init__(name="keep4mac", title=ICON_CHAR, quit_button=None)
        self._qt_app = qt_app
        self._panel = MainPanel()

        self.menu = [
            rumps.MenuItem("열기", callback=self._open),
            rumps.MenuItem("동기화", callback=self._sync),
            None,  # 구분선
            rumps.MenuItem("종료", callback=self._quit),
        ]

    # ── rumps 타이머: Qt 이벤트 루프 통합 ──────────────────────

    @rumps.timer(0.05)
    def _process_qt(self, _):
        """50ms마다 Qt 이벤트 처리 (rumps NSRunLoop 내에서 Qt 통합)."""
        QCoreApplication.processEvents()

    # ── 메뉴 액션 ──────────────────────────────────────────────

    def _open(self, _):
        if self._panel.isVisible():
            self._panel.hide()
        else:
            self._panel.show_near_menubar()

    def _sync(self, _):
        # Phase 7에서 실제 동기화 연동
        logger.info("수동 동기화 요청")
        rumps.notification("keep4mac", "", "동기화 기능은 Phase 7에서 구현됩니다.")

    def _quit(self, _):
        self._panel.hide()
        rumps.quit_application()
