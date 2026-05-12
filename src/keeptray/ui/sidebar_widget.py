import unicodedata

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QMenu, QPushButton, QSizePolicy, QVBoxLayout, QWidget

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
    lang_changed = pyqtSignal(str)  # lang code
    font_settings_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setFixedWidth(56)
        self.setStyleSheet("background: transparent;")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 14, 0, 14)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        self._new_note_btn  = self._make_btn("🗒", _("New Note"), self.new_note_requested)
        self._sync_btn      = self._make_btn("🔄", _("Sync"),     self.sync_requested)

        for btn in (self._new_note_btn, self._sync_btn):
            layout.addWidget(btn)

        layout.addStretch()

        self._archive_btn   = self._make_btn("📦", _("Archive"),   self.archive_requested)
        self._trash_btn     = self._make_btn("🗑", _("Trash"),     self.trash_requested)
        self._settings_btn  = self._make_btn("⚙️", _("Settings"), None)
        self._settings_btn.clicked.connect(self._on_settings_click)

        for btn in (self._archive_btn, self._trash_btn, self._settings_btn):
            layout.addWidget(btn)

    def retranslate_ui(self):
        """언어 변경 후 버튼 텍스트를 즉시 갱신한다."""
        self._new_note_btn.setText(f"🗒\n{self._wrap_label(_('New Note'))}")
        self._sync_btn.setText(f"🔄\n{self._wrap_label(_('Sync'))}")
        self._archive_btn.setText(f"📦\n{self._wrap_label(_('Archive'))}")
        self._trash_btn.setText(f"🗑\n{self._wrap_label(_('Trash'))}")
        self._settings_btn.setText(f"⚙️\n{self._wrap_label(_('Settings'))}")

    # ── 설정 메뉴 ─────────────────────────────────────────────

    def _on_settings_click(self):
        menu = QMenu(self)
        menu.setStyleSheet(_MENU_CSS)

        # 웹 Keep
        web_act = menu.addAction(f"🌐  {_('Web Keep')}")
        web_act.triggered.connect(lambda: self.open_web_requested.emit())

        # 자동시작 토글
        autostart_act = menu.addAction(f"🚀  {_('Autostart')}")
        autostart_act.setCheckable(True)
        autostart_act.setChecked(autostart.is_enabled())
        autostart_act.triggered.connect(self._on_autostart_toggle)

        menu.addSeparator()

        # 언어 변경 서브메뉴
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

        # 폰트 설정
        font_act = menu.addAction(f"🔤  {_('Font Settings…')}")
        font_act.triggered.connect(lambda: self.font_settings_requested.emit())

        menu.addSeparator()

        # 내 메일 주소
        from keeptray.core import settings as _settings
        my_email = _settings.get_my_email()
        email_label = f"✉  {_('My Email')}  ({my_email})" if my_email else f"✉  {_('My Email')}"
        my_email_act = menu.addAction(email_label)
        my_email_act.triggered.connect(self._on_set_my_email)

        menu.addSeparator()

        # 정보
        about_act = menu.addAction(f"ℹ️  {_('About')}")
        about_act.triggered.connect(lambda: self.about_requested.emit())

        # 로그아웃
        logout_act = menu.addAction(f"🚪  {_('Logout')}")
        logout_act.triggered.connect(lambda: self.logout_requested.emit())

        menu.addSeparator()

        # 종료
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
                background: #f2f2f7;
                border: 1px solid #d1d1d6;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                color: #1c1c1e;
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
        """52px 사이드바 버튼에 맞게 라벨 텍스트를 자동 줄바꿈한다.
        macOS 10px 폰트 실측 기준: CJK ≈ 12px, ASCII ≈ 7px."""
        def char_px(c: str) -> int:
            return 12 if unicodedata.east_asian_width(c) in ('W', 'F') else 7

        MAX_PX = 48  # 52px 버튼 - 좌우 패딩 4px = 콘텐츠 48px
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
