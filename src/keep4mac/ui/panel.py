from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MainPanel(QWidget):
    """트레이 아이콘 클릭 시 열리는 메인 패널 (Phase 4에서 내용 채워짐)."""

    closed = pyqtSignal()

    def __init__(self):
        super().__init__(
            flags=Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()

    def _build_ui(self):
        self.setFixedWidth(320)
        self.setMinimumHeight(400)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Phase 4에서 실제 노트 목록 위젯으로 교체
        placeholder = QLabel("⏳ 노트 목록 구현 중 (Phase 4)")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("color: #888; font-size: 14px; padding: 40px;")
        layout.addWidget(placeholder)

    def focusOutEvent(self, event):
        self.hide()
        self.closed.emit()
        super().focusOutEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            self.closed.emit()
        super().keyPressEvent(event)
