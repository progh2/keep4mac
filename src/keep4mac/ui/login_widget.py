import subprocess

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from keep4mac.api.keep_client import AuthError, KeepClient

_APP_PASSWORD_URL = "https://myaccount.google.com/apppasswords"
_2FA_URL = "https://myaccount.google.com/signinoptions/two-step-verification"


def _open_url(url: str) -> None:
    subprocess.run(["open", url], check=False)


class LoginWidget(QWidget):
    login_success = pyqtSignal()

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 24)
        layout.setSpacing(14)

        # 타이틀
        title = QLabel("keep4mac")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #202124;")
        layout.addWidget(title)

        sub = QLabel("Google Keep 메뉴바 앱")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size: 12px; color: #5f6368;")
        layout.addWidget(sub)

        layout.addSpacing(8)

        # ── 이메일 입력 ──────────────────────────────────────
        layout.addWidget(self._field_label("Google 계정 이메일"))
        self._email = QLineEdit()
        self._email.setPlaceholderText("example@gmail.com")
        self._email.setStyleSheet(self._input_css())
        self._email.textChanged.connect(self._update_open_btn)
        layout.addWidget(self._email)

        # ── 앱 비밀번호 만들기 박스 ──────────────────────────
        step1_box = QFrame()
        step1_box.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
            }
        """)
        box_layout = QVBoxLayout(step1_box)
        box_layout.setContentsMargins(14, 12, 14, 12)
        box_layout.setSpacing(6)

        step1_title = QLabel("① 앱 비밀번호 만들기")
        step1_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #202124; background: transparent;")
        box_layout.addWidget(step1_title)

        step1_desc = QLabel("Google이 이메일 대신 앱용 16자리\n비밀번호를 생성해줍니다.")
        step1_desc.setStyleSheet("font-size: 11px; color: #5f6368; background: transparent;")
        box_layout.addWidget(step1_desc)

        self._open_btn = QPushButton("Google 앱 비밀번호 페이지 열기  →")
        self._open_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8; color: white;
                border: none; border-radius: 6px;
                padding: 8px 12px; font-size: 12px;
                text-align: left;
            }
            QPushButton:hover { background: #1557b0; }
            QPushButton:disabled { background: #a0c3ff; }
        """)
        self._open_btn.setEnabled(False)
        self._open_btn.clicked.connect(self._open_app_password_page)
        box_layout.addWidget(self._open_btn)

        layout.addWidget(step1_box)

        # ── 앱 비밀번호 입력 ─────────────────────────────────
        layout.addWidget(self._field_label("② 앱 비밀번호 붙여넣기"))
        self._password = QLineEdit()
        self._password.setPlaceholderText("xxxx xxxx xxxx xxxx")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setStyleSheet(self._input_css())
        self._password.returnPressed.connect(self._do_login)
        layout.addWidget(self._password)

        # ── 오류 메시지 ──────────────────────────────────────
        self._error = QLabel()
        self._error.setStyleSheet("font-size: 12px; color: #ea4335;")
        self._error.setWordWrap(True)
        self._error.hide()
        layout.addWidget(self._error)

        # ── 로그인 버튼 ──────────────────────────────────────
        self._login_btn = QPushButton("로그인")
        self._login_btn.setStyleSheet("""
            QPushButton {
                background: #1a73e8; color: white;
                border: none; border-radius: 6px;
                padding: 10px; font-size: 14px; font-weight: 500;
            }
            QPushButton:hover { background: #1557b0; }
            QPushButton:disabled { background: #a0c3ff; }
        """)
        self._login_btn.clicked.connect(self._do_login)
        layout.addWidget(self._login_btn)

        # ── 2단계 인증 안내 ──────────────────────────────────
        note_layout = QHBoxLayout()
        note_layout.setContentsMargins(0, 0, 0, 0)
        note_icon = QLabel("ℹ️")
        note_icon.setFixedWidth(20)
        note_text = QLabel("앱 비밀번호는 Google 2단계 인증이 필요합니다.")
        note_text.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        note_link = QPushButton("설정하기 →")
        note_link.setStyleSheet("""
            QPushButton {
                background: transparent; color: #1a73e8;
                border: none; font-size: 11px; padding: 0;
            }
            QPushButton:hover { color: #1557b0; }
        """)
        note_link.clicked.connect(lambda: _open_url(_2FA_URL))
        note_layout.addWidget(note_icon)
        note_layout.addWidget(note_text)
        note_layout.addWidget(note_link)
        note_layout.addStretch()
        layout.addLayout(note_layout)

        layout.addStretch()

    # ── 이벤트 ───────────────────────────────────────────────

    def _update_open_btn(self, email: str):
        self._open_btn.setEnabled(bool(email.strip()))

    def _open_app_password_page(self):
        """이메일 입력 후 Google 앱 비밀번호 페이지를 브라우저로 열기."""
        _open_url(_APP_PASSWORD_URL)
        self._password.setFocus()

    def _do_login(self):
        email = self._email.text().strip()
        pw = self._password.text().replace(" ", "").strip()  # 공백 자동 제거

        if not email:
            self._show_error("Google 계정 이메일을 입력해주세요.")
            return
        if not pw:
            self._show_error("앱 비밀번호를 입력해주세요.")
            return

        self._login_btn.setEnabled(False)
        self._login_btn.setText("로그인 중…")
        self._error.hide()

        try:
            self._client.login(email, pw)
            self.login_success.emit()
        except AuthError as e:
            self._show_error(str(e))
        finally:
            self._login_btn.setEnabled(True)
            self._login_btn.setText("로그인")

    # ── 헬퍼 ─────────────────────────────────────────────────

    def _show_error(self, msg: str):
        self._error.setText(msg)
        self._error.show()

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #3c4043;")
        return lbl

    def _input_css(self) -> str:
        return """
            QLineEdit {
                border: 1px solid #dadce0; border-radius: 6px;
                padding: 9px 12px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #1a73e8; outline: none; }
        """
