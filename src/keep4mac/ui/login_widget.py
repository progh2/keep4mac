import subprocess

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
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

        # ── 고정 헤더 ─────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(88)
        header.setStyleSheet("background: #1a73e8;")
        hl = QVBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(2)
        hl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("🗒  keep4mac")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: white; background: transparent;"
        )
        hl.addWidget(title)

        subtitle = QLabel("Google Keep 메뉴바 앱")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 11px; color: rgba(255,255,255,0.85); background: transparent;"
        )
        hl.addWidget(subtitle)
        root.addWidget(header)

        # ── 스크롤 본문 ───────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: white; border: none; }")

        body = QWidget()
        body.setStyleSheet("background: white;")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        bl = QVBoxLayout(body)
        bl.setContentsMargins(20, 16, 20, 20)
        bl.setSpacing(10)

        # 이메일
        bl.addWidget(self._section_label("Google 계정 이메일"))
        self._email = self._make_input("example@gmail.com")
        self._email.textChanged.connect(self._on_email_changed)
        bl.addWidget(self._email)

        # Step 1 카드
        self._step1_btn = QPushButton("앱 비밀번호 페이지 열기  →")
        self._step1_btn.setMinimumHeight(38)
        self._step1_btn.setEnabled(False)
        self._step1_btn.setStyleSheet(self._btn_css(active=False))
        self._step1_btn.clicked.connect(self._open_step1)

        card1 = self._make_card(
            step="1",
            title="앱 비밀번호 발급",
            desc="Google에서 이 앱 전용 16자리 비밀번호를 발급받습니다.",
            inner=self._step1_btn,
        )
        bl.addWidget(card1)

        # Step 2 카드
        self._password = self._make_input("xxxx xxxx xxxx xxxx", password=True)
        self._password.returnPressed.connect(self._do_login)

        card2 = self._make_card(
            step="2",
            title="앱 비밀번호 입력",
            desc="발급받은 비밀번호를 붙여넣으세요. (공백 자동 제거)",
            inner=self._password,
        )
        bl.addWidget(card2)

        # 오류 메시지
        self._error = QLabel()
        self._error.setWordWrap(True)
        self._error.setStyleSheet(
            "font-size: 12px; color: #c5221f;"
            "background: #fce8e6; border-radius: 6px; padding: 8px 10px;"
        )
        self._error.hide()
        bl.addWidget(self._error)

        # 로그인 버튼
        self._login_btn = QPushButton("로그인")
        self._login_btn.setMinimumHeight(44)
        self._login_btn.setStyleSheet(self._btn_css(active=True, large=True))
        self._login_btn.clicked.connect(self._do_login)
        bl.addWidget(self._login_btn)

        # 2단계 인증 안내
        note_row = QHBoxLayout()
        note_row.setSpacing(4)
        note_row.setContentsMargins(0, 0, 0, 0)
        note_txt = QLabel("2단계 인증이 필요합니다.")
        note_txt.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        note_link = QPushButton("설정하기 →")
        note_link.setFlat(True)
        note_link.setCursor(Qt.CursorShape.PointingHandCursor)
        note_link.setStyleSheet(
            "font-size: 11px; color: #1a73e8; border: none;"
            "background: transparent; padding: 0;"
        )
        note_link.clicked.connect(lambda: _open_url(_2FA_URL))
        note_row.addWidget(note_txt)
        note_row.addWidget(note_link)
        note_row.addStretch()
        bl.addLayout(note_row)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

    # ── 이벤트 ────────────────────────────────────────────────

    def _on_email_changed(self, text: str):
        ok = bool(text.strip())
        self._step1_btn.setEnabled(ok)
        self._step1_btn.setStyleSheet(self._btn_css(active=ok))

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

    def _section_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #3c4043;")
        return lbl

    def _make_input(self, placeholder: str, password: bool = False) -> QLineEdit:
        w = QLineEdit()
        w.setPlaceholderText(placeholder)
        w.setFixedHeight(40)
        if password:
            w.setEchoMode(QLineEdit.EchoMode.Password)
        w.setStyleSheet("""
            QLineEdit {
                border: 1.5px solid #dadce0;
                border-radius: 8px;
                padding: 0 12px;
                font-size: 13px;
                color: #202124;
                background: white;
            }
            QLineEdit:focus { border-color: #1a73e8; }
        """)
        return w

    def _make_card(self, step: str, title: str, desc: str, inner: QWidget) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #e8eaed;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(6)

        # 배지 + 제목 행
        row = QHBoxLayout()
        row.setSpacing(8)
        row.setContentsMargins(0, 0, 0, 0)

        badge = QLabel(step)
        badge.setFixedSize(20, 20)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet(
            "background: #1a73e8; color: white; border-radius: 10px;"
            "font-size: 11px; font-weight: bold;"
        )

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #202124; background: transparent;"
        )

        row.addWidget(badge)
        row.addWidget(title_lbl)
        row.addStretch()
        layout.addLayout(row)

        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(
            "font-size: 11px; color: #5f6368; background: transparent;"
        )
        layout.addWidget(desc_lbl)
        layout.addWidget(inner)

        return card

    def _btn_css(self, active: bool = True, large: bool = False) -> str:
        size = "14px" if large else "12px"
        if not active:
            return f"""
                QPushButton {{
                    background: #e8eaed; color: #9aa0a6;
                    border: none; border-radius: 8px; font-size: {size};
                }}
            """
        return f"""
            QPushButton {{
                background: #1a73e8; color: white;
                border: none; border-radius: 8px;
                font-size: {size}; font-weight: 500;
            }}
            QPushButton:hover {{ background: #1557b0; }}
            QPushButton:pressed {{ background: #0d47a1; }}
            QPushButton:disabled {{ background: #e8eaed; color: #9aa0a6; }}
        """
