"""폰트 종류·크기 설정 다이얼로그 (모달리스 — 변경 즉시 앱에 반영)."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QFontComboBox, QFormLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QVBoxLayout,
)

from keeptray.core import settings as app_settings
from keeptray.i18n import gettext as _

_DLG_CSS = """
    QDialog { background: #ffffff; color: #1c1c1e; }
    QLabel  { color: #1c1c1e; font-size: 12px; }
    QFontComboBox, QSpinBox {
        background: #f2f2f7; border: 1px solid #d1d1d6;
        border-radius: 6px; padding: 4px 8px;
        font-size: 12px; color: #1c1c1e;
    }
    QFontComboBox:focus, QSpinBox:focus { border-color: #007AFF; background: #fff; }
"""

_ROWS = [
    ("list_title",   "목록 제목"),
    ("list_content", "목록 내용"),
    ("editor_title", "편집기 제목"),
    ("editor_body",  "편집기 본문"),
]


class FontSettingsDialog(QDialog):
    """모달리스 폰트 설정 창. 변경할 때마다 fonts_changed 시그널을 emit한다."""
    fonts_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Font Settings"))
        self.setMinimumWidth(420)
        self.setStyleSheet(_DLG_CSS)
        # 모달리스 + 항상 패널 위에 유지
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setWindowModality(Qt.WindowModality.NonModal)
        self._combos: dict[str, QFontComboBox] = {}
        self._spins: dict[str, QSpinBox] = {}
        self._orig_fonts: dict = app_settings.get_fonts()  # 열었을 때 원본
        self._block_signals = False
        self._build_ui()
        self._load_current()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 16, 20, 16)
        outer.setSpacing(12)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(8)

        for key, label in _ROWS:
            combo = QFontComboBox()
            combo.setMinimumWidth(200)
            combo.setMaximumWidth(240)

            spin = QSpinBox()
            spin.setRange(8, 36)
            spin.setSuffix(" pt")
            spin.setFixedWidth(72)

            row = QHBoxLayout()
            row.setSpacing(6)
            row.addWidget(combo, 1)
            row.addWidget(spin)

            form.addRow(label, row)
            self._combos[key] = combo
            self._spins[key] = spin

        outer.addLayout(form)

        # 미리보기
        self._preview = QLabel("가나다 ABC 123  Keep Note")
        self._preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._preview.setStyleSheet(
            "border: 1px solid #d1d1d6; border-radius: 6px;"
            "padding: 10px; background: #f9f9fb; color: #1c1c1e; font-size: 13px;"
        )
        outer.addWidget(self._preview)

        # 버튼 행
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        reset_btn = QPushButton(_("Restore Defaults"))
        reset_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #636366;"
            "border: 1px solid #d1d1d6; border-radius: 6px; font-size: 12px; padding: 4px 12px; }"
            "QPushButton:hover { background: #f2f2f7; }"
        )
        reset_btn.clicked.connect(self._on_reset)
        btn_row.addWidget(reset_btn)
        btn_row.addStretch()

        cancel_btn = QPushButton(_("Cancel"))
        cancel_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #636366;"
            "border: 1px solid #d1d1d6; border-radius: 6px; font-size: 13px; padding: 6px 16px; }"
            "QPushButton:hover { background: #f2f2f7; }"
        )
        cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(cancel_btn)

        close_btn = QPushButton(_("Close"))
        close_btn.setStyleSheet(
            "QPushButton { background: #007AFF; color: white;"
            "border: none; border-radius: 6px; font-size: 13px; padding: 6px 16px; }"
            "QPushButton:hover { background: #0066d6; }"
        )
        close_btn.clicked.connect(self.close)
        btn_row.addWidget(close_btn)

        outer.addLayout(btn_row)

        # 변경 시 즉시 반영
        for key in self._combos:
            self._combos[key].currentFontChanged.connect(self._on_changed)
            self._spins[key].valueChanged.connect(self._on_changed)

    def _load_current(self):
        self._block_signals = True
        fonts = app_settings.get_fonts()
        for key in self._combos:
            f = fonts[key]
            if f["family"]:
                self._combos[key].setCurrentFont(QFont(f["family"]))
            self._spins[key].setValue(f["size"])
        self._block_signals = False
        self._update_preview()

    def _on_changed(self):
        if self._block_signals:
            return
        fonts = self._current_fonts()
        app_settings.set_fonts(fonts)
        self._update_preview()
        self.fonts_changed.emit(fonts)

    def _update_preview(self):
        family = self._combos["editor_body"].currentFont().family()
        size = self._spins["editor_body"].value()
        family_css = f'font-family: "{family}";' if family else ""
        self._preview.setStyleSheet(
            f"border: 1px solid #d1d1d6; border-radius: 6px;"
            f"padding: 10px; background: #f9f9fb; color: #1c1c1e;"
            f"font-size: {size}px; {family_css}"
        )

    def _on_reset(self):
        self._block_signals = True
        defaults = app_settings.get_font_defaults()
        for key in self._combos:
            d = defaults[key]
            self._combos[key].setCurrentFont(QFont(d["family"]) if d["family"] else QFont())
            self._spins[key].setValue(d["size"])
        self._block_signals = False
        self._on_changed()

    def _on_cancel(self):
        """원본 설정으로 되돌리고 닫는다."""
        self._block_signals = True
        for key in self._combos:
            f = self._orig_fonts[key]
            self._combos[key].setCurrentFont(QFont(f["family"]) if f["family"] else QFont())
            self._spins[key].setValue(f["size"])
        self._block_signals = False
        app_settings.set_fonts(self._orig_fonts)
        self.fonts_changed.emit(self._orig_fonts)
        self.close()

    def _current_fonts(self) -> dict:
        return {
            key: {
                "family": self._combos[key].currentFont().family(),
                "size": self._spins[key].value(),
            }
            for key in self._combos
        }
