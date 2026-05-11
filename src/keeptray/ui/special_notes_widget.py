"""보관함 / 휴지통 노트 목록 위젯."""
import logging

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from keeptray.api.keep_client import KeepClient
from keeptray.core.models import NoteModel
from keeptray.i18n import gettext as _

logger = logging.getLogger(__name__)

_BTN_CSS = """
    QPushButton {{
        background: transparent;
        border: 1px solid {color};
        border-radius: 4px;
        color: {color};
        font-size: 11px;
        padding: 2px 8px;
    }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:pressed {{ background: {press}; }}
"""

_RESTORE_CSS = _BTN_CSS.format(color="#007AFF", hover="#e5f0ff", press="#cce0ff")
_DELETE_CSS  = _BTN_CSS.format(color="#FF3B30", hover="#ffe5e3", press="#ffccc9")
_UNARCH_CSS  = _BTN_CSS.format(color="#34C759", hover="#e5f9eb", press="#ccf2d7")


class _LoadThread(QThread):
    done = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, client: KeepClient, mode: str):
        super().__init__()
        self._client = client
        self._mode = mode

    def run(self):
        try:
            if self._mode == "archive":
                notes = self._client.get_archived_notes()
            else:
                notes = self._client.get_trashed_notes()
            self.done.emit(notes)
        except Exception as e:
            self.error.emit(str(e))


class SpecialNotesWidget(QWidget):
    """mode='archive' 또는 mode='trash'로 생성한다."""
    back_requested = pyqtSignal()
    notes_changed = pyqtSignal()   # 복원/삭제 후 목록 갱신 필요

    def __init__(self, client: KeepClient, mode: str):
        super().__init__()
        assert mode in ("archive", "trash")
        self._client = client
        self._mode = mode
        self._thread: _LoadThread | None = None
        self._build_ui()

    # ── UI 구성 ──────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 헤더
        header = QWidget()
        header.setFixedHeight(48)
        header.setStyleSheet("background: #f5f5f7; border-bottom: 1px solid #d1d1d6;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(8, 0, 8, 0)

        back_btn = QPushButton("←")
        back_btn.setFixedSize(32, 32)
        back_btn.setToolTip(_("Back"))
        back_btn.setStyleSheet(
            "QPushButton { background: transparent; border: none;"
            "font-size: 16px; color: #007AFF; }"
            "QPushButton:hover { background: #e5e5ea; border-radius: 8px; }"
        )
        back_btn.clicked.connect(self.back_requested)
        hl.addWidget(back_btn)

        if self._mode == "archive":
            title_text = _("📦  Archive")
        else:
            title_text = _("🗑  Trash")
        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1c1c1e;")
        hl.addWidget(title_lbl, 1)

        if self._mode == "trash":
            self._empty_btn = QPushButton(_("Empty Trash"))
            self._empty_btn.setStyleSheet(
                "QPushButton { background: transparent; border: none;"
                "color: #FF3B30; font-size: 12px; }"
                "QPushButton:hover { text-decoration: underline; }"
            )
            self._empty_btn.clicked.connect(self._on_empty_trash)
            hl.addWidget(self._empty_btn)

        root.addWidget(header)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #ffffff; }")

        self._body = QWidget()
        self._body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._layout = QVBoxLayout(self._body)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.setSpacing(6)
        self._layout.addStretch()

        scroll.setWidget(self._body)
        root.addWidget(scroll)

    # ── 데이터 ───────────────────────────────────────────────────

    def load(self):
        self._thread = _LoadThread(self._client, self._mode)
        self._thread.done.connect(self._render)
        self._thread.error.connect(lambda e: logger.warning("특수 목록 로드 실패: %s", e))
        self._thread.start()

    def _render(self, notes: list[NoteModel]):
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not notes:
            lbl = QLabel(_("No notes"))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #8e8e93; font-size: 13px; padding: 40px;")
            self._layout.insertWidget(0, lbl)
            return

        for i, note in enumerate(notes):
            card = self._make_card(note)
            self._layout.insertWidget(i, card)

    def _make_card(self, note: NoteModel) -> QWidget:
        outer = QFrame()
        outer.setStyleSheet(f"""
            QFrame {{
                background: {note.color_hex};
                border: 1px solid rgba(0,0,0,0.10);
                border-radius: 10px;
            }}
        """)
        ol = QVBoxLayout(outer)
        ol.setContentsMargins(12, 10, 12, 8)
        ol.setSpacing(4)

        if note.title:
            title = QLabel(note.title)
            title.setStyleSheet("font-size: 13px; font-weight: 600; color: #1c1c1e; background: transparent;")
            title.setWordWrap(True)
            ol.addWidget(title)

        preview = note.preview
        if preview:
            body = QLabel(preview)
            body.setStyleSheet("font-size: 12px; color: #636366; background: transparent;")
            body.setWordWrap(True)
            ol.addWidget(body)

        # 액션 버튼 행
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 4, 0, 0)
        btn_row.addStretch()

        if self._mode == "archive":
            btn = QPushButton(_("↩  Unarchive"))
            btn.setStyleSheet(_UNARCH_CSS)
            btn.clicked.connect(lambda checked=False, nid=note.id: self._on_unarchive(nid))
            btn_row.addWidget(btn)
        else:
            restore_btn = QPushButton(_("↩  Restore"))
            restore_btn.setStyleSheet(_RESTORE_CSS)
            restore_btn.clicked.connect(lambda checked=False, nid=note.id: self._on_restore(nid))
            btn_row.addWidget(restore_btn)

            del_btn = QPushButton(_("✕  Delete"))
            del_btn.setStyleSheet(_DELETE_CSS)
            del_btn.clicked.connect(lambda checked=False, nid=note.id: self._on_perm_delete(nid))
            btn_row.addWidget(del_btn)

        ol.addLayout(btn_row)
        return outer

    # ── 액션 ────────────────────────────────────────────────────

    def _on_unarchive(self, note_id: str):
        try:
            self._client.unarchive_note(note_id)
            self.notes_changed.emit()
            self.load()
        except Exception as e:
            logger.warning("보관 해제 실패: %s", e)

    def _on_restore(self, note_id: str):
        try:
            self._client.restore_note(note_id)
            self.notes_changed.emit()
            self.load()
        except Exception as e:
            logger.warning("복원 실패: %s", e)

    def _on_perm_delete(self, note_id: str):
        dlg = QMessageBox()
        dlg.setWindowTitle(_("Delete permanently"))
        dlg.setText(_("This note will be permanently deleted and cannot be recovered."))
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        dlg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if dlg.exec() == QMessageBox.StandardButton.Ok:
            try:
                self._client.permanently_delete_note(note_id)
                self.load()
            except Exception as e:
                logger.warning("영구 삭제 실패: %s", e)

    def _on_empty_trash(self):
        dlg = QMessageBox()
        dlg.setWindowTitle(_("Empty Trash"))
        dlg.setText(_("All notes in Trash will be permanently deleted."))
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        dlg.setDefaultButton(QMessageBox.StandardButton.Cancel)
        if dlg.exec() == QMessageBox.StandardButton.Ok:
            try:
                self._client.empty_trash()
                self.notes_changed.emit()
                self.load()
            except Exception as e:
                logger.warning("휴지통 비우기 실패: %s", e)
