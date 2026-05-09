from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QVBoxLayout, QWidget

_BTN_CSS = """
    QPushButton {{
        background: transparent;
        border: none;
        color: #5f6368;
        font-size: 10px;
        padding: 4px 2px;
    }}
    QPushButton:hover {{
        background: #e0e0e0;
        border-radius: 8px;
        color: #202124;
    }}
    QPushButton:pressed {{
        background: #d0d0d0;
        border-radius: 8px;
    }}
"""


class SidebarWidget(QWidget):
    new_note_requested = pyqtSignal()
    sync_requested = pyqtSignal()
    open_web_requested = pyqtSignal()
    logout_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(60)
        self.setStyleSheet("background: #f1f3f4; border-right: 1px solid #e0e0e0;")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        for icon, label, signal in [
            ("🗒", "새 노트", self.new_note_requested),
            ("↻", "동기화", self.sync_requested),
            ("🌐", "웹 Keep", self.open_web_requested),
        ]:
            layout.addWidget(self._make_btn(icon, label, signal))

        layout.addStretch()

        for icon, label, signal in [
            ("↩", "로그아웃", self.logout_requested),
            ("✕", "종료", self.quit_requested),
        ]:
            layout.addWidget(self._make_btn(icon, label, signal))

    def _make_btn(self, icon: str, label: str, signal) -> QPushButton:
        btn = QPushButton(f"{icon}\n{label}")
        btn.setFixedSize(56, 52)
        btn.setStyleSheet(_BTN_CSS)
        btn.clicked.connect(lambda: signal.emit())
        return btn
