from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from keep4mac.core.models import NoteModel


class NoteItemWidget(QFrame):
    clicked = pyqtSignal(str)  # note_id

    def __init__(self, note: NoteModel):
        super().__init__()
        self._note_id = note.id
        self._build_ui(note)
        self._apply_style(note.color_hex)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _build_ui(self, note: NoteModel):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)

        # 제목 행
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(4)

        if note.pinned:
            pin_label = QLabel("📌")
            pin_label.setFixedWidth(18)
            pin_label.setStyleSheet("font-size: 11px;")
            title_row.addWidget(pin_label)

        title_text = note.title if note.title else "(제목 없음)"
        title_label = QLabel(title_text)
        title_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #202124; background: transparent;")
        title_label.setMaximumWidth(270)
        title_row.addWidget(title_label, 1)
        layout.addLayout(title_row)

        # 미리보기
        preview = note.preview
        if preview:
            preview_label = QLabel(preview)
            preview_label.setStyleSheet("font-size: 12px; color: #5f6368; background: transparent;")
            preview_label.setMaximumHeight(34)
            preview_label.setWordWrap(True)
            layout.addWidget(preview_label)

    def _apply_style(self, bg_hex: str):
        self.setStyleSheet(f"""
            NoteItemWidget {{
                background: {bg_hex};
                border: 1px solid rgba(0,0,0,0.10);
                border-radius: 8px;
            }}
            NoteItemWidget:hover {{
                border: 1px solid rgba(0,0,0,0.28);
            }}
        """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._note_id)
        super().mousePressEvent(event)
