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
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 헤더 영역 ──────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(100)
        header.setStyleSheet("background: #1a73e8; border-radius: 0px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("🗒  keep4mac")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; background: transparent;")
        h_layout.addWidget(title)

        subtitle = QLabel("Google Keep 메뉴바 앱")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.8); background: transparent;")
        h_layout.addWidget(subtitle)

        root.addWidget(header)

        # ── 본문 영역 ──────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: #ffffff;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 20, 20, 20)
        body_layout.setSpacing(12)

        # 이메일
        body_layout.addWidget(self._label("Google 계정 이메일"))
        self._email = self._input("example@gmail.com")
        self._email.textChanged.connect(self._update_step1_btn)
        body_layout.addWidget(self._email)

        # STEP 1 카드
        card1 = self._make_card(
            step="1",
            title="앱 비밀번호 발급",
            desc="Google에서 이 앱 전용 비밀번호를\n발급받아 사용합니다.",
        )
        self._step1_btn = QPushButton("앱 비밀번호 페이지 열기  →")
        self._step1_btn.setEnabled(False)
        self._step1_btn.setMinimumHeight(40)
        self._step1_btn.setStyleSheet(self._primary_btn_css(disabled=True))
        self._step1_btn.clicked.connect(self._open_step1)
        card1.layout().addWidget(self._step1_btn)
        body_layout.addWidget(card1)

        # STEP 2 카드
        card2 = self._make_card(
            step="2",
            title="앱 비밀번호 입력",
            desc="발급받은 16자리 비밀번호를 입력하세요.",
        )
        self._password = self._input("xxxx xxxx xxxx xxxx", password=True)
        self._password.returnPressed.connect(self._do_login)
        card2.layout().addWidget(self._password)
        body_layout.addWidget(card2)

        # 오류 메시지
        self._error = QLabel()
        self._error.setWordWrap(True)
        self._error.setStyleSheet(
            "font-size: 12px; color: #ea4335; "
            "background: #fce8e6; border-radius: 6px; padding: 8px 10px;"
        )
        self._error.hide()
        body_layout.addWidget(self._error)

        # 로그인 버튼
        self._login_btn = QPushButton("로그인")
        self._login_btn.setMinimumHeight(46)
        self._login_btn.setStyleSheet(self._primary_btn_css())
        self._login_btn.clicked.connect(self._do_login)
        body_layout.addWidget(self._login_btn)

        # 2단계 인증 안내
        note = QHBoxLayout()
        note.setSpacing(4)
        note_txt = QLabel("앱 비밀번호는 Google 2단계 인증이 필요합니다.")
        note_txt.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        note_link = QPushButton("설정하기 →")
        note_link.setFlat(True)
        note_link.setCursor(Qt.CursorShape.PointingHandCursor)
        note_link.setStyleSheet(
            "font-size: 11px; color: #1a73e8; border: none; "
            "background: transparent; padding: 0;"
        )
        note_link.clicked.connect(lambda: _open_url(_2FA_URL))
        note.addWidget(note_txt)
        note.addWidget(note_link)
        note.addStretch()
        body_layout.addLayout(note)

        body_layout.addStretch()
        root.addWidget(body)

    # ── 이벤트 ────────────────────────────────────────────────

    def _update_step1_btn(self, email: str):
        ok = bool(email.strip())
        self._step1_btn.setEnabled(ok)
        self._step1_btn.setStyleSheet(self._primary_btn_css(disabled=not ok))

    def _open_step1(self):
        _open_url(_APP_PASSWORD_URL)
        self._password.setFocus()

    def _do_login(self):
        email = self._email.text().strip()
        pw = self._password.text().replace(" ", "").strip()

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

    def _show_error(self, msg: str):
        self._error.setText(msg)
        self._error.show()

    # ── 위젯 헬퍼 ────────────────────────────────────────────

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #3c4043;")
        return lbl

    def _input(self, placeholder: str, password: bool = False) -> QLineEdit:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setMinimumHeight(40)
        if password:
            w.setEchoMode(QLineEdit.EchoMode.Password)
        w.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #dadce0;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 13px;
                color: #202124;
            }
            QLineEdit:focus {
                border-color: #1a73e8;
            }
        """)
        return w

    def _make_card(self, step: str, title: str, desc: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #e8eaed;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 14)
        layout.setSpacing(8)

        # 스텝 배지 + 제목
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        badge = QLabel(step)
        badge.setFixedSize(22, 22)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("""
            background: #1a73e8; color: white;
            border-radius: 11px;
            font-size: 11px; font-weight: bold;
        """)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #202124; background: transparent;"
        )

        header_row.addWidget(badge)
        header_row.addWidget(title_lbl)
        header_row.addStretch()
        layout.addLayout(header_row)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            "font-size: 11px; color: #5f6368; background: transparent;"
        )
        layout.addWidget(desc_lbl)

        return card

    def _primary_btn_css(self, disabled: bool = False) -> str:
        if disabled:
            return """
                QPushButton {
                    background: #e8eaed; color: #9aa0a6;
                    border: none; border-radius: 8px;
                    font-size: 13px; font-weight: 500;
                }
            """
        return """
            QPushButton {
                background: #1a73e8; color: white;
                border: none; border-radius: 8px;
                font-size: 13px; font-weight: 500;
            }
            QPushButton:hover { background: #1557b0; }
            QPushButton:pressed { background: #0d47a1; }
            QPushButton:disabled { background: #e8eaed; color: #9aa0a6; }
        """
