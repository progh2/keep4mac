from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from keep4mac.api.keep_client import KeepClient, SyncError
from keep4mac.core.models import NoteModel
from keep4mac.ui.note_item_widget import NoteItemWidget


class NoteListWidget(QWidget):
    note_selected = pyqtSignal(str)   # note_id
    new_note_requested = pyqtSignal()

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client
        self._all_notes: list[NoteModel] = []
        self._build_ui()

    # ── UI 구성 ───────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 0)
        outer.setSpacing(0)

        # 검색바
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  검색…")
        self._search.textChanged.connect(self._filter)
        self._search.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dadce0;
                border-radius: 18px;
                padding: 6px 16px;
                font-size: 13px;
                background: #f1f3f4;
            }
            QLineEdit:focus { background: #fff; border-color: #1a73e8; }
        """)
        outer.addWidget(self._search)
        outer.addSpacing(8)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._list_body = QWidget()
        self._list_body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._list_layout = QVBoxLayout(self._list_body)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_body)
        outer.addWidget(scroll)

        # 하단 바
        bar = QHBoxLayout()
        bar.setContentsMargins(4, 8, 4, 8)

        new_btn = QPushButton("＋  새 노트")
        new_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8; color: white;
                border: none; border-radius: 6px;
                padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background: #1557b0; }
        """)
        new_btn.clicked.connect(self.new_note_requested)

        self._sync_label = QLabel("")
        self._sync_label.setStyleSheet("font-size: 11px; color: #9aa0a6;")

        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedWidth(28)
        refresh_btn.setToolTip("동기화")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #5f6368;
                border: 1px solid #dadce0; border-radius: 4px; font-size: 14px;
            }
            QPushButton:hover { background: #f1f3f4; }
        """)
        refresh_btn.clicked.connect(self.refresh)

        bar.addWidget(new_btn)
        bar.addStretch()
        bar.addWidget(self._sync_label)
        bar.addSpacing(4)
        bar.addWidget(refresh_btn)
        outer.addLayout(bar)

    # ── 데이터 ────────────────────────────────────────────────

    def load_notes(self):
        """Keep 서버 동기화 후 목록 갱신."""
        try:
            self._client.sync()
            self._sync_label.setText("방금 동기화")
        except SyncError:
            self._sync_label.setText("동기화 실패")

        self._all_notes = self._client.get_notes()
        self._render(self._all_notes)

    def refresh(self):
        self.load_notes()

    # ── 검색 ─────────────────────────────────────────────────

    def _filter(self, query: str):
        if not query:
            self._render(self._all_notes)
            return
        q = query.lower()
        filtered = [
            n for n in self._all_notes
            if q in n.title.lower() or q in n.text.lower()
        ]
        self._render(filtered)

    # ── 렌더링 ────────────────────────────────────────────────

    def _render(self, notes: list[NoteModel]):
        # 기존 아이템 제거 (stretch 제외)
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not notes:
            lbl = QLabel("노트가 없습니다")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9aa0a6; font-size: 13px; padding: 40px;")
            self._list_layout.insertWidget(0, lbl)
            return

        pinned = [n for n in notes if n.pinned]
        regular = [n for n in notes if not n.pinned]
        idx = 0

        if pinned:
            self._list_layout.insertWidget(idx, self._section_header("📌  고정됨")); idx += 1
            for note in pinned:
                w = NoteItemWidget(note)
                w.clicked.connect(self.note_selected)
                self._list_layout.insertWidget(idx, w); idx += 1

        if regular:
            if pinned:
                self._list_layout.insertWidget(idx, self._section_header("메모")); idx += 1
            for note in regular:
                w = NoteItemWidget(note)
                w.clicked.connect(self.note_selected)
                self._list_layout.insertWidget(idx, w); idx += 1

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #9aa0a6; padding: 6px 2px 2px 2px;"
        )
        return lbl
