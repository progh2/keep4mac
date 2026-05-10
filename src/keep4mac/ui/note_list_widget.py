from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QLabel, QLineEdit,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from keep4mac.api.keep_client import KeepClient, SyncError
from keep4mac.core.models import NoteModel
from keep4mac.i18n import gettext as _
from keep4mac.ui.note_item_widget import NoteItemWidget


class NoteListWidget(QWidget):
    note_selected = pyqtSignal(str)   # note_id

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
        self._search.setPlaceholderText(_("🔍  Search…"))
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
        scroll.setStyleSheet("QScrollArea { background: #ffffff; }")

        self._list_body = QWidget()
        self._list_body.setAutoFillBackground(True)
        self._list_body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._list_layout = QVBoxLayout(self._list_body)
        self._list_layout.setContentsMargins(0, 0, 4, 0)
        self._list_layout.setSpacing(4)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_body)
        outer.addWidget(scroll)

    # ── 데이터 ────────────────────────────────────────────────

    def retranslate_ui(self):
        self._search.setPlaceholderText(_("🔍  Search…"))
        self._render(self._all_notes)

    def load_notes(self):
        """Keep 서버 동기화 후 목록 갱신."""
        try:
            self._client.sync()
        except SyncError:
            pass
        self._all_notes = self._client.get_notes()
        self._render(self._all_notes)

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
            lbl = QLabel(_("No notes"))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #9aa0a6; font-size: 13px; padding: 40px;")
            self._list_layout.insertWidget(0, lbl)
            return

        pinned = [n for n in notes if n.pinned]
        regular = [n for n in notes if not n.pinned]
        idx = 0

        if pinned:
            self._list_layout.insertWidget(idx, self._section_header(_("📌  Pinned"))); idx += 1
            for note in pinned:
                w = NoteItemWidget(note, fetch_fn=self._client.fetch_image)
                w.clicked.connect(self.note_selected)
                self._list_layout.insertWidget(idx, w); idx += 1

        if regular:
            if pinned:
                self._list_layout.insertWidget(idx, self._section_header(_("Notes"))); idx += 1
            for note in regular:
                w = NoteItemWidget(note, fetch_fn=self._client.fetch_image)
                w.clicked.connect(self.note_selected)
                self._list_layout.insertWidget(idx, w); idx += 1

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 11px; font-weight: bold; color: #9aa0a6; padding: 6px 2px 2px 2px;"
        )
        return lbl
