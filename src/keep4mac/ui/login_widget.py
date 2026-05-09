from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QLabel, QPushButton, QSizePolicy,
    QVBoxLayout, QWidget,
)

from keep4mac.api.keep_client import AuthError, KeepClient


class _BrowserLoginThread(QThread):
    success = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.result: tuple | None = None  # (email, sapisid, cookies)

    def run(self):
        from keep4mac.api.playwright_auth import run_browser_login
        try:
            self.result = run_browser_login()
            self.success.emit()
        except Exception as e:
            self.failed.emit(str(e))


class LoginWidget(QWidget):
    login_success = pyqtSignal()

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client
        self._thread: _BrowserLoginThread | None = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 헤더 ──────────────────────────────────────────────
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

        # ── 본문 ──────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet("background: white;")
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        bl = QVBoxLayout(body)
        bl.setContentsMargins(24, 32, 24, 32)
        bl.setSpacing(16)
        bl.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 안내 카드
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #f8f9fa;
                border: 1px solid #e8eaed;
                border-radius: 10px;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(6)

        card_title = QLabel("Google 계정으로 로그인")
        card_title.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #202124; background: transparent;"
        )
        cl.addWidget(card_title)

        card_desc = QLabel(
            "버튼을 누르면 Chrome 창이 열립니다.\n"
            "Google 계정으로 로그인하면 자동으로 연결됩니다."
        )
        card_desc.setWordWrap(True)
        card_desc.setStyleSheet(
            "font-size: 12px; color: #5f6368; background: transparent;"
        )
        cl.addWidget(card_desc)
        bl.addWidget(card)

        # 로그인 버튼
        self._login_btn = QPushButton("Google로 로그인")
        self._login_btn.setMinimumHeight(46)
        self._login_btn.setStyleSheet(self._btn_css(active=True))
        self._login_btn.clicked.connect(self._do_login)
        bl.addWidget(self._login_btn)

        # 오류 메시지
        self._error = QLabel()
        self._error.setWordWrap(True)
        self._error.setStyleSheet(
            "font-size: 12px; color: #c5221f;"
            "background: #fce8e6; border-radius: 6px; padding: 8px 10px;"
        )
        self._error.hide()
        bl.addWidget(self._error)

        root.addWidget(body, 1)

    # ── 이벤트 ───────────────────────────────────────────────

    def _do_login(self):
        self._login_btn.setEnabled(False)
        self._login_btn.setText("브라우저 열리는 중…")
        self._error.hide()

        self._thread = _BrowserLoginThread()
        self._thread.success.connect(self._on_browser_success)
        self._thread.failed.connect(self._on_browser_failed)
        self._thread.start()

    def _on_browser_success(self):
        email, sapisid, cookies, api_key = self._thread.result
        try:
            self._client.login_with_browser(email, sapisid, cookies, api_key)
            self.login_success.emit()
        except AuthError as e:
            self._show_error(str(e))
        finally:
            self._reset_button()

    def _on_browser_failed(self, error: str):
        self._show_error(error)
        self._reset_button()

    def _reset_button(self):
        self._login_btn.setEnabled(True)
        self._login_btn.setText("Google로 로그인")

    def _show_error(self, msg: str):
        self._error.setText(msg)
        self._error.show()

    # ── 스타일 ───────────────────────────────────────────────

    def _btn_css(self, active: bool = True) -> str:
        if not active:
            return """
                QPushButton {
                    background: #e8eaed; color: #9aa0a6;
                    border: none; border-radius: 8px; font-size: 14px;
                }
            """
        return """
            QPushButton {
                background: #1a73e8; color: white;
                border: none; border-radius: 8px;
                font-size: 14px; font-weight: 500;
            }
            QPushButton:hover { background: #1557b0; }
            QPushButton:pressed { background: #0d47a1; }
            QPushButton:disabled { background: #e8eaed; color: #9aa0a6; }
        """
