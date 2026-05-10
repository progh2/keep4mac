import logging

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QLabel, QLineEdit,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from keep4mac.api.keep_client import KeepClient, SyncError
from keep4mac.core.models import NoteModel
from keep4mac.i18n import gettext as _
from keep4mac.ui.note_item_widget import NoteItemWidget

logger = logging.getLogger(__name__)


class _SyncThread(QThread):
    """백그라운드에서 Keep 동기화 후 노트 목록을 반환한다."""
    done = pyqtSignal(list)   # list[NoteModel]
    error = pyqtSignal(str)

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client

    def run(self):
        try:
            self._client.sync()
            notes = self._client.get_notes()
            self.done.emit(notes)
        except SyncError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))


class NoteListWidget(QWidget):
    note_selected = pyqtSignal(str)   # note_id

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client
        self._all_notes: list[NoteModel] = []
        self._sync_thread: _SyncThread | None = None
        self._syncing = False
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
                border: 1px solid #d1d1d6;
                border-radius: 18px;
                padding: 6px 16px;
                font-size: 13px;
                background: #f2f2f7;
            }
            QLineEdit:focus { background: #fff; border-color: #007AFF; }
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

    def load_notes(self, force_sync: bool = False):
        """캐시로 즉시 표시 후 백그라운드에서 동기화한다.

        force_sync=True 이면 쿨다운을 무시하고 즉시 동기화한다 (↻ 버튼 전용).
        """
        # 1단계: 메모리 캐시로 즉시 표시
        cached = self._client.get_cached_notes()
        if cached:
            self._all_notes = cached
            self._render(cached)

        # 2단계: 동기화 필요 여부 확인
        if not force_sync and not self._client.needs_sync:
            return

        # 3단계: 이미 동기화 중이면 스킵
        if self._syncing:
            return

        self._syncing = True
        self._sync_thread = _SyncThread(self._client)
        self._sync_thread.done.connect(self._on_sync_done)
        self._sync_thread.error.connect(self._on_sync_error)
        self._sync_thread.finished.connect(self._on_sync_finished)
        self._sync_thread.start()

    def _on_sync_done(self, notes: list[NoteModel]):
        self._all_notes = notes
        self._render(notes)

    def _on_sync_error(self, msg: str):
        logger.warning("백그라운드 동기화 실패: %s", msg)

    def _on_sync_finished(self):
        self._syncing = False

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
            lbl.setStyleSheet("color: #8e8e93; font-size: 13px; padding: 40px;")
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
            "font-size: 11px; font-weight: bold; color: #8e8e93; padding: 6px 2px 2px 2px;"
        )
        return lbl
