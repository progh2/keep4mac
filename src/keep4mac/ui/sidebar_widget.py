from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QMenu, QPushButton, QVBoxLayout, QWidget

from keep4mac.core import autostart
import keep4mac.i18n as i18n
from keep4mac.i18n import gettext as _

_BTN_CSS = """
    QPushButton {{
        background: transparent;
        border: none;
        color: #9aa0a6;
        font-size: 10px;
        padding: 4px 2px;
        border-radius: 6px;
    }}
    QPushButton:hover {{
        background: #f1f3f4;
        color: #3c4043;
    }}
    QPushButton:pressed {{
        background: #e8eaed;
        color: #202124;
    }}
"""

_AUTOSTART_ON_CSS = """
    QPushButton {
        background: #e8f0fe;
        border: none;
        color: #1a73e8;
        font-size: 10px;
        padding: 4px 2px;
        border-radius: 6px;
    }
    QPushButton:hover { background: #d2e3fc; }
    QPushButton:pressed { background: #c5d9fb; }
"""


class SidebarWidget(QWidget):
    new_note_requested = pyqtSignal()
    sync_requested = pyqtSignal()
    open_web_requested = pyqtSignal()
    about_requested = pyqtSignal()
    logout_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    lang_changed = pyqtSignal(str)  # lang code

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

        self._new_note_btn = self._make_btn("🗒", _("New Note"), self.new_note_requested)
        self._sync_btn     = self._make_btn("↻",  _("Sync"),     self.sync_requested)
        self._web_btn      = self._make_btn("🌐", _("Web Keep"), self.open_web_requested)

        for btn in (self._new_note_btn, self._sync_btn, self._web_btn):
            layout.addWidget(btn)

        layout.addStretch()

        self._autostart_btn = QPushButton()
        self._autostart_btn.setFixedSize(52, 50)
        self._autostart_btn.clicked.connect(self._on_autostart_toggle)
        layout.addWidget(self._autostart_btn)
        self._refresh_autostart_btn()

        self._lang_btn = self._make_btn("🌏", _("Language"), None)
        self._lang_btn.clicked.connect(self._on_lang_click)
        layout.addWidget(self._lang_btn)

        self._about_btn  = self._make_btn("?",  _("About"),   self.about_requested)
        self._logout_btn = self._make_btn("↩",  _("Logout"),  self.logout_requested)
        self._quit_btn   = self._make_btn("✕",  _("Quit"),    self.quit_requested)

        for btn in (self._about_btn, self._logout_btn, self._quit_btn):
            layout.addWidget(btn)

    def retranslate_ui(self):
        """언어 변경 후 모든 버튼 텍스트를 즉시 갱신한다."""
        self._new_note_btn.setText(f"🗒\n{_('New Note')}")
        self._sync_btn.setText(f"↻\n{_('Sync')}")
        self._web_btn.setText(f"🌐\n{_('Web Keep')}")
        self._lang_btn.setText(f"🌏\n{_('Language')}")
        self._about_btn.setText(f"?\n{_('About')}")
        self._logout_btn.setText(f"↩\n{_('Logout')}")
        self._quit_btn.setText(f"✕\n{_('Quit')}")
        self._refresh_autostart_btn()

    def _refresh_autostart_btn(self):
        enabled = autostart.is_enabled()
        self._autostart_btn.setText(_("🚀\nAutostart"))
        self._autostart_btn.setStyleSheet(
            _AUTOSTART_ON_CSS if enabled else _BTN_CSS.format()
        )
        self._autostart_btn.setToolTip(
            _("Autostart enabled (click to disable)")
            if enabled else
            _("Start at login (click to enable)")
        )

    def _on_autostart_toggle(self):
        autostart.toggle()
        self._refresh_autostart_btn()

    def _on_lang_click(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: white;
                border: 1px solid #dadce0;
                border-radius: 8px;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected { background: #f1f3f4; color: #202124; }
            QMenu::item:disabled { color: #1a73e8; font-weight: 600; }
        """)

        current = i18n.current_lang()
        for code, name in i18n.SUPPORTED_LANGS.items():
            label = f"✓ {name}" if code == current else f"   {name}"
            action = menu.addAction(label)
            action.setData(code)
            if code == current:
                action.setEnabled(False)

        pos = self._lang_btn.mapToGlobal(self._lang_btn.rect().topRight())
        action = menu.exec(pos)
        if action and action.isEnabled():
            lang = action.data()
            i18n.save_lang(lang)
            self.lang_changed.emit(lang)

    def _make_btn(self, icon: str, label: str, signal) -> QPushButton:
        btn = QPushButton(f"{icon}\n{label}")
        btn.setFixedSize(52, 50)
        btn.setStyleSheet(_BTN_CSS)
        if signal is not None:
            btn.clicked.connect(lambda: signal.emit())
        return btn
