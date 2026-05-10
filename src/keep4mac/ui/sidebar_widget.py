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

        for icon, label, signal in [
            ("🗒", _("New Note"), self.new_note_requested),
            ("↻", _("Sync"), self.sync_requested),
            ("🌐", _("Web Keep"), self.open_web_requested),
        ]:
            layout.addWidget(self._make_btn(icon, label, signal))

        layout.addStretch()

        self._autostart_btn = QPushButton()
        self._autostart_btn.setFixedSize(52, 50)
        self._autostart_btn.clicked.connect(self._on_autostart_toggle)
        layout.addWidget(self._autostart_btn)
        self._refresh_autostart_btn()

        self._lang_btn = self._make_btn("🌏", _("Language"), None)
        self._lang_btn.clicked.disconnect()
        self._lang_btn.clicked.connect(self._on_lang_click)
        layout.addWidget(self._lang_btn)

        for icon, label, signal in [
            ("?", _("About"), self.about_requested),
            ("↩", _("Logout"), self.logout_requested),
            ("✕", _("Quit"), self.quit_requested),
        ]:
            layout.addWidget(self._make_btn(icon, label, signal))

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
        btn.clicked.connect(lambda: signal.emit())
        return btn
