import logging

from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from keep4mac.ui.icons import make_status_icon, make_tray_icon
from keep4mac.ui.panel import MainPanel

logger = logging.getLogger(__name__)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app
        self._panel = MainPanel()

        self.setIcon(make_tray_icon())
        self.setToolTip("keep4mac")
        self._build_menu()

        self.activated.connect(self._on_activated)

    # ── 메뉴 구성 ─────────────────────────────────────────────

    def _build_menu(self):
        menu = QMenu()

        open_action = QAction("열기", self)
        open_action.triggered.connect(self._toggle_panel)
        menu.addAction(open_action)

        self._sync_action = QAction("동기화", self)
        self._sync_action.triggered.connect(self._on_sync)
        menu.addAction(self._sync_action)

        menu.addSeparator()

        quit_action = QAction("종료", self)
        quit_action.triggered.connect(self._app.quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)

    # ── 이벤트 핸들러 ──────────────────────────────────────────

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_panel()

    def _toggle_panel(self):
        if self._panel.isVisible():
            self._panel.hide()
        else:
            self._show_panel()

    def _show_panel(self):
        geo: QRect = self.geometry()
        screen = self._app.primaryScreen().geometry()

        # 트레이 아이콘 아래에 패널 배치
        x = geo.x() - self._panel.width() // 2 + geo.width() // 2
        y = geo.y() + geo.height() + 4

        # 화면 경계 보정
        x = max(4, min(x, screen.width() - self._panel.width() - 4))
        y = max(4, min(y, screen.height() - self._panel.minimumHeight() - 4))

        self._panel.move(x, y)
        self._panel.show()
        self._panel.raise_()
        self._panel.activateWindow()
        self._panel.setFocus()

    def _on_sync(self):
        # Phase 7 동기화 연동 시 실제 구현
        self.set_status("syncing")
        logger.info("수동 동기화 요청")

    # ── 상태 아이콘 ────────────────────────────────────────────

    def set_status(self, state: str):
        """state: 'normal' | 'syncing' | 'error'"""
        self.setIcon(make_status_icon(state))

    # ── 패널 접근자 ────────────────────────────────────────────

    @property
    def panel(self) -> MainPanel:
        return self._panel
