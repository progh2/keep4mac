"""폰트 종류·크기 설정 다이얼로그."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QFontComboBox, QFormLayout, QHBoxLayout,
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("Font Settings"))
        self.setMinimumWidth(400)
        self.setStyleSheet(_DLG_CSS)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._combos: dict[str, QFontComboBox] = {}
        self._spins: dict[str, QSpinBox] = {}
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

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.setStyleSheet("color: #1c1c1e;")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        btn_row.addWidget(buttons)

        outer.addLayout(btn_row)

        # 미리보기 업데이트 연결
        for key in self._combos:
            self._combos[key].currentFontChanged.connect(self._update_preview)
            self._spins[key].valueChanged.connect(self._update_preview)

    def _load_current(self):
        fonts = app_settings.get_fonts()
        for key in self._combos:
            f = fonts[key]
            if f["family"]:
                self._combos[key].setCurrentFont(self._combos[key].currentFont().__class__(f["family"]))
            self._spins[key].setValue(f["size"])
        self._update_preview()

    def _update_preview(self):
        # 편집기 본문 폰트로 미리보기 갱신
        family = self._combos["editor_body"].currentFont().family()
        size = self._spins["editor_body"].value()
        family_css = f'font-family: "{family}";' if family else ""
        self._preview.setStyleSheet(
            f"border: 1px solid #d1d1d6; border-radius: 6px;"
            f"padding: 10px; background: #f9f9fb; color: #1c1c1e;"
            f"font-size: {size}px; {family_css}"
        )

    def _on_reset(self):
        defaults = app_settings.get_font_defaults()
        for key in self._combos:
            d = defaults[key]
            if d["family"]:
                from PyQt6.QtGui import QFont
                self._combos[key].setCurrentFont(QFont(d["family"]))
            else:
                from PyQt6.QtGui import QFont
                self._combos[key].setCurrentFont(QFont())
            self._spins[key].setValue(d["size"])

    def get_fonts(self) -> dict:
        return {
            key: {
                "family": self._combos[key].currentFont().family(),
                "size": self._spins[key].value(),
            }
            for key in self._combos
        }
