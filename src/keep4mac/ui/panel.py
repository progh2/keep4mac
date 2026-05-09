from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette, QScreen
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget


class MainPanel(QWidget):
    """트레이 메뉴 '열기' 클릭 시 표시되는 메인 패널."""

    def __init__(self):
        super().__init__(
            flags=Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setFixedWidth(320)
        self.setMinimumHeight(400)
        self._build_ui()
        self._apply_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Phase 4에서 실제 노트 목록 위젯으로 교체
        placeholder = QLabel("⏳ 노트 목록 구현 중\n(Phase 4)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; font-size: 14px; padding: 40px;")
        layout.addWidget(placeholder)

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
            }
        """)

    def show_near_menubar(self):
        """화면 우상단 메뉴바 아래에 패널 배치."""
        screen: QScreen = QApplication.primaryScreen()
        sg = screen.availableGeometry()  # 메뉴바 제외한 영역

        # 메뉴바 바로 아래, 오른쪽 끝 기준 배치
        x = sg.right() - self.width() - 8
        y = sg.top() + 4

        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
