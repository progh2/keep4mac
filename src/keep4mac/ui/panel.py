from PyQt6.QtCore import Qt
from PyQt6.QtGui import QScreen
from PyQt6.QtWidgets import QApplication, QStackedWidget, QWidget

from keep4mac.api.keep_client import KeepClient
from keep4mac.ui.login_widget import LoginWidget
from keep4mac.ui.note_list_widget import NoteListWidget

_IDX_LOGIN = 0
_IDX_NOTES = 1


class MainPanel(QWidget):
    def __init__(self, client: KeepClient):
        super().__init__(
            flags=Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._client = client
        self.setFixedWidth(320)
        self.setMinimumHeight(480)
        self._build_ui()
        self.setStyleSheet("""
            QWidget#MainPanel {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 10px;
            }
        """)
        self.setObjectName("MainPanel")

    def _build_ui(self):
        self._stack = QStackedWidget(self)

        self._login_w = LoginWidget(self._client)
        self._login_w.login_success.connect(self._on_login_success)

        self._notes_w = NoteListWidget(self._client)
        self._notes_w.note_selected.connect(self._on_note_selected)
        self._notes_w.new_note_requested.connect(self._on_new_note)

        self._stack.addWidget(self._login_w)   # index 0
        self._stack.addWidget(self._notes_w)   # index 1

        # QStackedWidget이 MainPanel 전체를 채우게 설정
        self._stack.setGeometry(0, 0, self.width(), self.minimumHeight())

    def resizeEvent(self, event):
        self._stack.resize(self.size())
        super().resizeEvent(event)

    # ── 표시 ─────────────────────────────────────────────────

    def show_near_menubar(self):
        """화면 우상단 (메뉴바 바로 아래)에 패널 배치 후 표시."""
        screen: QScreen = QApplication.primaryScreen()
        sg = screen.availableGeometry()

        x = sg.right() - self.width() - 8
        y = sg.top() + 4
        self.move(x, y)

        # 인증 상태에 따라 화면 전환
        if self._client.is_logged_in:
            self._show_notes()
        else:
            self._stack.setCurrentIndex(_IDX_LOGIN)

        self.show()
        self.raise_()
        self.activateWindow()

    def _show_notes(self):
        self._stack.setCurrentIndex(_IDX_NOTES)
        self._notes_w.load_notes()

    # ── 슬롯 ─────────────────────────────────────────────────

    def _on_login_success(self):
        self._show_notes()

    def _on_note_selected(self, note_id: str):
        # Phase 5에서 상세 뷰 연결
        print(f"노트 선택됨: {note_id}")

    def _on_new_note(self):
        # Phase 5에서 새 노트 편집 뷰 연결
        print("새 노트 요청됨")

    # ── 키 처리 ──────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
