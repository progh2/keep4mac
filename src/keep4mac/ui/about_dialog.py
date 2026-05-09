from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from keep4mac import __version__
from keep4mac.i18n import gettext as _

_GITHUB_REPO = "https://github.com/progh2/keep4mac"
_GITHUB_PROFILE = "https://github.com/progh2"


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(_("About keep4mac"))
        self.setFixedSize(300, 260)
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint
        )
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 헤더
        header = QWidget()
        header.setFixedHeight(90)
        header.setStyleSheet("background: #1a73e8;")
        hl = QVBoxLayout(header)
        hl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.setSpacing(4)

        icon = QLabel("🗒")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 28px; background: transparent;")
        hl.addWidget(icon)

        title = QLabel("keep4mac")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: white; background: transparent;"
        )
        hl.addWidget(title)
        layout.addWidget(header)

        # 본문
        body = QWidget()
        body.setStyleSheet("background: white;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 20, 24, 20)
        bl.setSpacing(10)
        bl.setAlignment(Qt.AlignmentFlag.AlignTop)

        version_lbl = QLabel(f"{_('Version')} {__version__}")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_lbl.setStyleSheet("font-size: 12px; color: #9aa0a6;")
        bl.addWidget(version_lbl)

        desc = QLabel(_("Google Keep Menu Bar App"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("font-size: 13px; color: #3c4043;")
        bl.addWidget(desc)

        bl.addSpacing(4)

        made_by = QLabel(_("Made by"))
        made_by.setAlignment(Qt.AlignmentFlag.AlignCenter)
        made_by.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        bl.addWidget(made_by)

        author_btn = QPushButton("progh2")
        author_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        author_btn.setStyleSheet("""
            QPushButton {
                background: transparent; border: none;
                font-size: 13px; font-weight: 600; color: #1a73e8;
            }
            QPushButton:hover { color: #1557b0; }
        """)
        author_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_GITHUB_PROFILE)))
        bl.addWidget(author_btn)

        bl.addStretch()

        # 버튼 행
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        github_btn = QPushButton("GitHub")
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.setFixedHeight(34)
        github_btn.setStyleSheet("""
            QPushButton {
                background: #f1f3f4; border: none; border-radius: 6px;
                font-size: 12px; color: #3c4043;
            }
            QPushButton:hover { background: #e8eaed; }
        """)
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_GITHUB_REPO)))
        btn_row.addWidget(github_btn)

        close_btn = QPushButton(_("Close"))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8; border: none; border-radius: 6px;
                font-size: 12px; color: white;
            }
            QPushButton:hover { background: #1557b0; }
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        bl.addLayout(btn_row)
        layout.addWidget(body, 1)
