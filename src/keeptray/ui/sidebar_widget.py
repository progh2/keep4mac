import unicodedata

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QMenu, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from keeptray.core import autostart
import keeptray.i18n as i18n
from keeptray.i18n import gettext as _

_BTN_CSS = """
    QPushButton {{
        background: transparent;
        border: none;
        color: #8e8e93;
        font-size: 10px;
        padding: 4px 2px;
        border-radius: 6px;
    }}
    QPushButton:hover {{
        background: #f2f2f7;
        color: #1c1c1e;
    }}
    QPushButton:pressed {{
        background: #e5e5ea;
        color: #1c1c1e;
    }}
"""

_BTN_ACTIVE_CSS = """
    QPushButton {{
        background: #e8f0fe;
        border: none;
        color: #1a73e8;
        font-size: 10px;
        padding: 4px 2px;
        border-radius: 6px;
    }}
    QPushButton:hover {{ background: #d2e3fc; color: #1a73e8; }}
    QPushButton:pressed {{ background: #c5d9f9; }}
"""

_MENU_CSS = """
    QMenu {
        background: white;
        border: 1px solid #d1d1d6;
        border-radius: 8px;
        padding: 4px;
        font-size: 12px;
    }
    QMenu::item {
        padding: 6px 16px;
        border-radius: 4px;
    }
    QMenu::item:selected { background: #f2f2f7; color: #1c1c1e; }
    QMenu::item:disabled { color: #007AFF; font-weight: 600; }
    QMenu::separator { height: 1px; background: #d1d1d6; margin: 4px 8px; }
    QMenu::right-arrow { image: none; width: 8px; }
"""


class SidebarWidget(QWidget):
    new_note_requested = pyqtSignal()
    sync_requested = pyqtSignal()
    archive_requested = pyqtSignal()
    trash_requested = pyqtSignal()
    open_web_requested = pyqtSignal()
    about_requested = pyqtSignal()
    logout_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    lang_changed = pyqtSignal(str)
    font_settings_requested = pyqtSignal()
    label_selected = pyqtSignal(str)          # label_id, 빈 문자열 = 전체
    label_manager_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(56)
        self.setStyleSheet("background: transparent;")
        self._active_label: str = ""
        self._label_btns: dict[str, QPushButton] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 14, 0, 14)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._new_note_btn = self._make_btn("🗒", _("New Note"), self.new_note_requested)
        self._sync_btn     = self._make_btn("🔄", _("Sync"),     self.sync_requested)
        layout.addWidget(self._new_note_btn)
        layout.addWidget(self._sync_btn)

        # ── 구분선 ──────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #e5e5ea; margin: 4px 6px;")
        layout.addWidget(sep)

        # ── 라벨 스크롤 영역 ────────────────────────────
        self._label_scroll = QScrollArea()
        self._label_scroll.setWidgetResizable(True)
        self._label_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._label_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._label_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._label_scroll.setStyleSheet("""
            QScrollArea { background: transparent; }
            QScrollBar:vertical {
                width: 4px; background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #c7c7cc; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self._label_scroll.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )
        self._label_scroll.setFixedWidth(56)

        self._label_container = QWidget()
        self._label_container.setStyleSheet("background: transparent;")
        self._label_layout = QVBoxLayout(self._label_container)
        self._label_layout.setContentsMargins(0, 0, 0, 0)
        self._label_layout.setSpacing(2)
        self._label_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop
        )
        self._label_scroll.setWidget(self._label_container)
        layout.addWidget(self._label_scroll, 1)   # stretch=1 → 여유 공간 차지

        # ── 고정 하단 버튼 ──────────────────────────────
        self._archive_btn  = self._make_btn("📦", _("Archive"),  self.archive_requested)
        self._trash_btn    = self._make_btn("🗑",  _("Trash"),    self.trash_requested)
        self._settings_btn = self._make_btn("⚙️", _("Settings"), None)
        self._settings_btn.clicked.connect(self._on_settings_click)

        for btn in (self._archive_btn, self._trash_btn, self._settings_btn):
            layout.addWidget(btn)

    # ── 라벨 목록 갱신 ────────────────────────────────────────

    def set_labels(self, labels: list[dict]):
        """동기화 후 라벨 목록을 갱신한다."""
        # 기존 버튼 제거
        while self._label_layout.count():
            item = self._label_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._label_btns.clear()

        for lbl in labels:
            btn = self._make_label_btn(lbl["id"], lbl["name"])
            self._label_layout.addWidget(btn)
            self._label_btns[lbl["id"]] = btn

        # 선택 상태 유지 또는 초기화
        if self._active_label not in self._label_btns:
            self._active_label = ""
        self._refresh_label_styles()

    def clear_label_selection(self):
        self._active_label = ""
        self._refresh_label_styles()

    def _make_label_btn(self, label_id: str, name: str) -> QPushButton:
        btn = QPushButton(f"🏷\n{self._wrap_label(name)}")
        btn.setFixedWidth(52)
        btn.setMinimumHeight(44)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        btn.setStyleSheet(_BTN_CSS)
        btn.clicked.connect(lambda: self._on_label_click(label_id))
        return btn

    def _on_label_click(self, label_id: str):
        if self._active_label == label_id:
            self._active_label = ""   # 재클릭 시 해제
        else:
            self._active_label = label_id
        self._refresh_label_styles()
        self.label_selected.emit(self._active_label)

    def _refresh_label_styles(self):
        for lid, btn in self._label_btns.items():
            btn.setStyleSheet(
                _BTN_ACTIVE_CSS if lid == self._active_label else _BTN_CSS
            )

    # ── retranslate ───────────────────────────────────────────

    def retranslate_ui(self):
        self._new_note_btn.setText(f"🗒\n{self._wrap_label(_('New Note'))}")
        self._sync_btn.setText(f"🔄\n{self._wrap_label(_('Sync'))}")
        self._archive_btn.setText(f"📦\n{self._wrap_label(_('Archive'))}")
        self._trash_btn.setText(f"🗑\n{self._wrap_label(_('Trash'))}")
        self._settings_btn.setText(f"⚙️\n{self._wrap_label(_('Settings'))}")

    # ── 설정 메뉴 ─────────────────────────────────────────────

    def _on_settings_click(self):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_CSS)

        web_act = menu.addAction(f"🌐  {_('Web Keep')}")
        web_act.triggered.connect(lambda: self.open_web_requested.emit())

        autostart_act = menu.addAction(f"🚀  {_('Autostart')}")
        autostart_act.setCheckable(True)
        autostart_act.setChecked(autostart.is_enabled())
        autostart_act.triggered.connect(self._on_autostart_toggle)

        menu.addSeparator()

        lang_menu = menu.addMenu(f"🌏  {_('Language')}")
        lang_menu.setStyleSheet(_MENU_CSS)
        current = i18n.current_lang()
        for code, name in i18n.SUPPORTED_LANGS.items():
            label = f"✓  {name}" if code == current else f"    {name}"
            act = lang_menu.addAction(label)
            if code == current:
                act.setEnabled(False)
            else:
                act.triggered.connect(
                    lambda checked=False, c=code: self._on_lang_select(c)
                )

        font_act = menu.addAction(f"🔤  {_('Font Settings…')}")
        font_act.triggered.connect(lambda: self.font_settings_requested.emit())

        label_act = menu.addAction(f"🏷  {_('Label Management…')}")
        label_act.triggered.connect(lambda: self.label_manager_requested.emit())

        menu.addSeparator()

        from keeptray.core import settings as _settings
        my_email = _settings.get_my_email()
        email_label = f"✉  {_('My Email')}  ({my_email})" if my_email else f"✉  {_('My Email')}"
        my_email_act = menu.addAction(email_label)
        my_email_act.triggered.connect(self._on_set_my_email)

        menu.addSeparator()

        about_act = menu.addAction(f"ℹ️  {_('About')}")
        about_act.triggered.connect(lambda: self.about_requested.emit())

        logout_act = menu.addAction(f"🚪  {_('Logout')}")
        logout_act.triggered.connect(lambda: self.logout_requested.emit())

        menu.addSeparator()

        quit_act = menu.addAction(f"✖️  {_('Quit')}")
        quit_act.triggered.connect(lambda: self.quit_requested.emit())

        pos = self._settings_btn.mapToGlobal(self._settings_btn.rect().topRight())
        menu.exec(pos)

    def _on_autostart_toggle(self):
        autostart.toggle()

    def _on_set_my_email(self):
        from PyQt6.QtWidgets import (
            QDialog, QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout,
        )
        from keeptray.core import settings as _settings

        current = _settings.get_my_email()
        dlg = QDialog()
        dlg.setWindowTitle(_("My Email"))
        dlg.setFixedWidth(320)
        dlg.setStyleSheet("QDialog { background: #ffffff; color: #1c1c1e; }")

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        lbl = QLabel(_("Enter your email address:"))
        lbl.setStyleSheet("color: #1c1c1e; font-size: 12px;")
        layout.addWidget(lbl)

        edit = QLineEdit(current or "")
        edit.setStyleSheet("""
            QLineEdit {
                background: #f2f2f7; border: 1px solid #d1d1d6;
                border-radius: 6px; padding: 6px 10px;
                font-size: 13px; color: #1c1c1e;
            }
            QLineEdit:focus { border-color: #007AFF; background: #fff; }
        """)
        layout.addWidget(edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet("color: #1c1c1e;")
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            _settings.set_my_email(edit.text().strip())

    def _on_lang_select(self, code: str):
        i18n.save_lang(code)
        self.lang_changed.emit(code)

    # ── 공통 헬퍼 ─────────────────────────────────────────────

    @staticmethod
    def _wrap_label(label: str) -> str:
        def char_px(c: str) -> int:
            return 12 if unicodedata.east_asian_width(c) in ('W', 'F') else 7
        MAX_PX = 48
        total_px = sum(char_px(c) for c in label)
        if total_px <= MAX_PX:
            return label
        if ' ' in label:
            return '\n'.join(label.split(' ', 1))
        mid = len(label) // 2
        return label[:mid] + '\n' + label[mid:]

    def _make_btn(self, icon: str, label: str, signal) -> QPushButton:
        btn = QPushButton(f"{icon}\n{self._wrap_label(label)}")
        btn.setFixedWidth(52)
        btn.setMinimumHeight(50)
        btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        btn.setStyleSheet(_BTN_CSS)
        if signal is not None:
            btn.clicked.connect(lambda: signal.emit())
        return btn
