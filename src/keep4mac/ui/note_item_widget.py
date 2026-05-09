from typing import Callable

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from keep4mac.core.models import NoteModel, NoteType
from keep4mac.core.url_utils import extract_urls, short_url


class _ImageThread(QThread):
    done = pyqtSignal(bytes)

    def __init__(self, url: str, fetch_fn: Callable[[str], bytes | None]):
        super().__init__()
        self._url = url
        self._fetch_fn = fetch_fn

    def run(self):
        data = self._fetch_fn(self._url)
        if data:
            self.done.emit(data)


class NoteItemWidget(QFrame):
    clicked = pyqtSignal(str)  # note_id

    def __init__(self, note: NoteModel, fetch_fn: Callable[[str], bytes | None] | None = None):
        super().__init__()
        self._note_id = note.id
        self._fetch_fn = fetch_fn
        self._img_label: QLabel | None = None
        self._img_thread: _ImageThread | None = None
        self._copy_btn: QPushButton | None = None
        self._clip_text = self._build_clip_text(note)
        self._build_ui(note)
        self._apply_style(note.color_hex)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if note.image_url and fetch_fn:
            self._load_image(note.image_url)

    @staticmethod
    def _build_clip_text(note: NoteModel) -> str:
        parts = [p for p in [note.title, note.content] if p]
        return "\n".join(parts)

    def _build_ui(self, note: NoteModel):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 이미지 영역
        if note.image_url:
            self._img_label = QLabel()
            self._img_label.setFixedHeight(130)
            self._img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._img_label.setStyleSheet("background: #e8eaed;")
            layout.addWidget(self._img_label)

        # 텍스트 영역
        text_w = QFrame()
        tl = QVBoxLayout(text_w)
        tl.setContentsMargins(12, 10, 12, 10)
        tl.setSpacing(4)

        # 제목 행
        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(4)

        if note.pinned:
            pin_label = QLabel("📌")
            pin_label.setFixedWidth(18)
            pin_label.setStyleSheet("font-size: 11px;")
            title_row.addWidget(pin_label)

        if note.title or note.pinned:
            title_label = QLabel(note.title)
            title_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #202124; background: transparent;")
            title_label.setWordWrap(True)
            title_row.addWidget(title_label, 1)

        self._copy_btn = QPushButton("📋")
        self._copy_btn.setFixedSize(22, 22)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 12px; border-radius: 4px;
            }
            QPushButton:hover { background: rgba(0,0,0,0.08); }
            QPushButton:pressed { background: rgba(0,0,0,0.14); }
        """)
        self._copy_btn.setToolTip("클립보드에 복사")
        self._copy_btn.clicked.connect(self._copy_to_clipboard)
        self._copy_btn.hide()
        title_row.addWidget(self._copy_btn)

        tl.addLayout(title_row)

        # 전체 내용
        content = note.content
        if content:
            content_label = QLabel(content)
            content_label.setStyleSheet("font-size: 12px; color: #5f6368; background: transparent;")
            content_label.setWordWrap(True)
            tl.addWidget(content_label)

        # 링크 인디케이터
        all_text = note.text + " ".join(i.text for i in note.checklist_items)
        urls = extract_urls(all_text)
        if urls:
            link_row = QHBoxLayout()
            link_row.setContentsMargins(0, 2, 0, 0)
            link_row.setSpacing(4)
            link_icon = QLabel("🔗")
            link_icon.setStyleSheet("font-size: 11px; background: transparent;")
            link_row.addWidget(link_icon)
            suffix = f" 외 {len(urls) - 1}개" if len(urls) > 1 else ""
            link_lbl = QLabel(short_url(urls[0], 36) + suffix)
            link_lbl.setStyleSheet("font-size: 11px; color: #1a73e8; background: transparent;")
            link_row.addWidget(link_lbl, 1)
            tl.addLayout(link_row)

        layout.addWidget(text_w)

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

    def _load_image(self, url: str):
        self._img_thread = _ImageThread(url, self._fetch_fn)
        self._img_thread.done.connect(self._on_image_ready)
        self._img_thread.start()

    def _on_image_ready(self, data: bytes):
        if self._img_label is None:
            return
        pixmap = QPixmap()
        pixmap.loadFromData(data)
        if pixmap.isNull():
            return
        w = self._img_label.width() or 270
        h = self._img_label.height()
        scaled = pixmap.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)
        self._img_label.setPixmap(scaled)

    def enterEvent(self, event):
        if self._copy_btn:
            self._copy_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self._copy_btn:
            self._copy_btn.hide()
        super().leaveEvent(event)

    def _copy_to_clipboard(self):
        QApplication.clipboard().setText(self._clip_text)
        if self._copy_btn:
            self._copy_btn.setText("✓")
            QTimer.singleShot(1500, lambda: self._copy_btn.setText("📋") if self._copy_btn else None)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._note_id)
        super().mousePressEvent(event)
