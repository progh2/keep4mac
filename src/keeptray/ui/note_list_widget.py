import dataclasses
import logging
from datetime import timezone

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QMenu,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from keeptray.api.keep_client import AuthError, KeepClient, SyncError
from keeptray.core import settings as app_settings
from keeptray.core.models import COLOR_HEX, NoteColor, NoteModel
from keeptray.i18n import gettext as _
from keeptray.ui.note_item_widget import NoteItemWidget

logger = logging.getLogger(__name__)


class _SyncThread(QThread):
    """백그라운드에서 Keep 동기화 후 노트 목록을 반환한다."""
    done = pyqtSignal(list)   # list[NoteModel]
    error = pyqtSignal(str)
    auth_expired = pyqtSignal()

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client

    def run(self):
        try:
            self._client.sync()
            notes = self._client.get_notes()
            self.done.emit(notes)
        except AuthError:
            self.auth_expired.emit()
        except SyncError as e:
            self.error.emit(str(e))
        except Exception as e:
            self.error.emit(str(e))


class NoteListWidget(QWidget):
    note_selected = pyqtSignal(str)   # note_id
    sync_done = pyqtSignal()          # 동기화 완료 (라벨 갱신용)
    auth_expired = pyqtSignal()       # 세션 만료 → 로그아웃 안내

    # 정렬 키 레이블 매핑 (key → 표시 이름 함수)
    _SORT_LABELS: dict[str, str] = {
        "updated": "수정일",
        "created": "생성일",
        "title": "제목",
    }

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client
        self._all_notes: list[NoteModel] = []
        self._sync_thread: _SyncThread | None = None
        self._syncing = False
        self._sort = app_settings.get_sort()
        self._filter_label_id: str = ""
        self._filter_color: NoteColor | None = None
        self._color_btns: dict[NoteColor, QPushButton] = {}
        self._build_ui()

    # ── UI 구성 ───────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 0)
        outer.setSpacing(0)

        # 검색바 + 정렬 버튼 행
        search_row = QHBoxLayout()
        search_row.setSpacing(6)

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
        search_row.addWidget(self._search)

        self._sort_btn = QPushButton("↕")
        self._sort_btn.setFixedSize(32, 32)
        self._sort_btn.setToolTip(_("Sort"))
        self._sort_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #d1d1d6;
                border-radius: 16px;
                background: #f2f2f7;
                font-size: 14px;
                color: #3c3c43;
            }
            QPushButton:hover { background: #e5e5ea; }
            QPushButton:pressed { background: #d1d1d6; }
        """)
        self._sort_btn.clicked.connect(self._show_sort_menu)
        search_row.addWidget(self._sort_btn)

        outer.addLayout(search_row)

        # 오프라인 배너
        self._offline_banner = QLabel()
        self._offline_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._offline_banner.setStyleSheet("""
            QLabel {
                background: #FF9500;
                color: white;
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 6px;
            }
        """)
        self._offline_banner.hide()
        outer.addSpacing(4)
        outer.addWidget(self._offline_banner)

        # 색상 필터 팔레트 (DEFAULT 제외 11색 + 전체 해제 버튼)
        color_row = QHBoxLayout()
        color_row.setContentsMargins(2, 4, 2, 0)
        color_row.setSpacing(4)
        color_row.addStretch()
        _PALETTE = [c for c in NoteColor if c != NoteColor.DEFAULT]
        for color in _PALETTE:
            btn = QPushButton()
            btn.setFixedSize(16, 16)
            btn.setToolTip(color.name.capitalize())
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_HEX[color]};
                    border: 1.5px solid rgba(0,0,0,0.18);
                    border-radius: 8px;
                }}
                QPushButton:hover {{ border-color: rgba(0,0,0,0.45); }}
            """)
            btn.clicked.connect(lambda _, c=color: self._on_color_filter(c))
            self._color_btns[color] = btn
            color_row.addWidget(btn)
        color_row.addStretch()
        outer.addLayout(color_row)
        outer.addSpacing(4)

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
        self._sort_btn.setToolTip(_("Sort"))
        self._render(self._all_notes)

    def apply_theme(self):
        from keeptray.core.theme import get_colors
        c = get_colors()
        self._search.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {c['border']};
                border-radius: 18px;
                padding: 6px 16px;
                font-size: 13px;
                background: {c['surface2']};
                color: {c['text']};
            }}
            QLineEdit:focus {{ background: {c['surface']}; border-color: {c['accent']}; }}
        """)
        self._sort_btn.setStyleSheet(f"""
            QPushButton {{
                border: 1px solid {c['border']};
                border-radius: 16px;
                background: {c['surface2']};
                font-size: 14px;
                color: {c['text2']};
            }}
            QPushButton:hover {{ background: {c['border2']}; }}
        """)
        self._list_body.setStyleSheet(f"background: {c['surface']};")

    # ── 정렬 ─────────────────────────────────────────────────

    def _show_sort_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #ffffff; border: 1px solid #d1d1d6; border-radius: 8px; padding: 4px; }
            QMenu::item { padding: 6px 20px; font-size: 13px; border-radius: 4px; }
            QMenu::item:selected { background: #007AFF; color: #ffffff; }
        """)

        entries = [
            ("updated", True,  _("Modified (Newest)")),
            ("updated", False, _("Modified (Oldest)")),
            ("created", True,  _("Created (Newest)")),
            ("created", False, _("Created (Oldest)")),
            ("title",   False, _("Title (A→Z)")),
            ("title",   True,  _("Title (Z→A)")),
        ]
        for key, desc, label in entries:
            prefix = "✓ " if self._sort["key"] == key and self._sort["desc"] == desc else "   "
            act = menu.addAction(prefix + label)
            act.setData((key, desc))

        chosen = menu.exec(self._sort_btn.mapToGlobal(self._sort_btn.rect().bottomLeft()))
        if chosen and chosen.data():
            key, desc = chosen.data()
            self._sort = {"key": key, "desc": desc}
            app_settings.set_sort(key, desc)
            query = self._search.text()
            if query:
                self._filter(query)
            else:
                self._render(self._all_notes)

    def _sorted(self, notes: list[NoteModel]) -> list[NoteModel]:
        key = self._sort["key"]
        desc = self._sort["desc"]
        _epoch = 0.0

        def sort_key(n: NoteModel):
            if key == "title":
                return n.title.lower()
            if key == "created":
                dt = n.created
            else:
                dt = n.updated
            if dt is None:
                return _epoch
            if dt.tzinfo is None:
                ts = dt.replace(tzinfo=timezone.utc).timestamp()
            else:
                ts = dt.timestamp()
            return ts

        return sorted(notes, key=sort_key, reverse=desc)

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
        self._sync_thread.auth_expired.connect(self._on_auth_expired)
        self._sync_thread.finished.connect(self._on_sync_finished)
        self._sync_thread.start()

    def filter_by_label(self, label_id: str):
        """라벨 필터를 설정하고 현재 노트 목록을 다시 렌더링한다."""
        self._filter_label_id = label_id
        self._apply_filters()

    def _on_color_filter(self, color: NoteColor):
        if self._filter_color == color:
            self._filter_color = None
        else:
            self._filter_color = color
        for c, btn in self._color_btns.items():
            selected = (c == self._filter_color)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {COLOR_HEX[c]};
                    border: {('2.5px solid #1c1c1e' if selected else '1.5px solid rgba(0,0,0,0.18)')};
                    border-radius: 8px;
                }}
                QPushButton:hover {{ border-color: rgba(0,0,0,0.45); }}
            """)
        self._apply_filters()

    def update_note_labels(self, note_id: str, label_ids: list[str]):
        """노트 편집기에서 라벨 변경 시 즉시 _all_notes를 갱신하고 필터를 재적용한다."""
        self._all_notes = [
            dataclasses.replace(n, label_ids=label_ids) if n.id == note_id else n
            for n in self._all_notes
        ]
        self._apply_filters()

    def _apply_filters(self):
        notes = self._all_notes
        if self._filter_label_id:
            notes = [n for n in notes if self._filter_label_id in n.label_ids]
        if self._filter_color is not None:
            notes = [n for n in notes if n.color == self._filter_color]
        query = self._search.text()
        if query:
            q = query.lower()
            notes = [n for n in notes if q in n.title.lower() or q in n.text.lower()]
        self._render(notes)

    def _on_sync_done(self, notes: list[NoteModel]):
        self._all_notes = notes
        self._apply_filters()
        self._offline_banner.hide()
        self.sync_done.emit()

    def _on_sync_error(self, msg: str):
        logger.warning("백그라운드 동기화 실패: %s", msg)
        self._offline_banner.setText(f"⚠  {_('Offline')} — {_('Showing cached notes')}")
        self._offline_banner.show()

    def _on_auth_expired(self):
        self._offline_banner.setText(f"🔒  {_('Session expired')} — {_('Please log in again')}")
        self._offline_banner.setStyleSheet("""
            QLabel {
                background: #FF3B30;
                color: white;
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 6px;
            }
        """)
        self._offline_banner.show()
        self.auth_expired.emit()

    def _on_sync_finished(self):
        self._syncing = False

    # ── 검색 ─────────────────────────────────────────────────

    def _filter(self, query: str):
        self._apply_filters()

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

        pinned = self._sorted([n for n in notes if n.pinned])
        regular = self._sorted([n for n in notes if not n.pinned])
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
