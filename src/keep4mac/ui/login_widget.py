from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget,
)

from keep4mac.api.keep_client import AuthError, KeepClient


class LoginWidget(QWidget):
    login_success = pyqtSignal()

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 36, 24, 24)
        layout.setSpacing(12)

        title = QLabel("keep4mac")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #202124;")
        layout.addWidget(title)

        subtitle = QLabel("Google Keep 메뉴바 앱")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #5f6368;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        self._email = QLineEdit()
        self._email.setPlaceholderText("Google 이메일")
        self._email.setStyleSheet(self._input_style())
        layout.addWidget(self._email)

        self._password = QLineEdit()
        self._password.setPlaceholderText("앱 비밀번호 (16자리)")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setStyleSheet(self._input_style())
        self._password.returnPressed.connect(self._do_login)
        layout.addWidget(self._password)

        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: #ea4335; font-size: 12px;")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        self._login_btn = QPushButton("로그인")
        self._login_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8; color: white;
                border: none; border-radius: 6px;
                padding: 10px; font-size: 14px;
            }
            QPushButton:hover  { background: #1557b0; }
            QPushButton:disabled { background: #a0c3ff; }
        """)
        self._login_btn.clicked.connect(self._do_login)
        layout.addWidget(self._login_btn)

        hint = QLabel("앱 비밀번호: Google 계정 → 보안 → 앱 비밀번호")
        hint.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        layout.addStretch()

    def _input_style(self) -> str:
        return """
            QLineEdit {
                border: 1px solid #dadce0; border-radius: 6px;
                padding: 8px 12px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #1a73e8; }
        """

    def _do_login(self):
        email = self._email.text().strip()
        password = self._password.text().strip()

        if not email or not password:
            self._show_error("이메일과 비밀번호를 입력해주세요.")
            return

        self._login_btn.setEnabled(False)
        self._login_btn.setText("로그인 중…")
        self._error_label.hide()

        try:
            self._client.login(email, password)
            self.login_success.emit()
        except AuthError as e:
            self._show_error(str(e))
        finally:
            self._login_btn.setEnabled(True)
            self._login_btn.setText("로그인")

    def _show_error(self, msg: str):
        self._error_label.setText(msg)
        self._error_label.show()
