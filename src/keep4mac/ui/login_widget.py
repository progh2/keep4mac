import os
import subprocess

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog, QFrame, QLabel, QLineEdit, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from keep4mac.api.keep_client import AuthError, KeepClient
from keep4mac.api.oauth_flow import CONFIG_DIR, CREDENTIALS_FILE, OAuthError, OAuthFlow

# ── OAuth 워커 스레드 ──────────────────────────────────────────────

class _OAuthWorker(QThread):
    success = pyqtSignal(str, str)   # email, access_token
    error = pyqtSignal(str)

    def run(self):
        try:
            email, token = OAuthFlow().authenticate()
            self.success.emit(email, token)
        except Exception as e:
            self.error.emit(str(e))


# ── 설정 안내 뷰 ──────────────────────────────────────────────────

class _SetupGuideWidget(QWidget):
    """credentials.json 설정 단계 안내."""

    done = pyqtSignal()   # 파일 선택 완료 → 로그인 뷰로 돌아가기

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("Google OAuth 설정")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #202124;")
        layout.addWidget(title)

        steps = QLabel(
            "1. Google Cloud Console 접속\n"
            "2. 프로젝트 생성 (또는 기존 선택)\n"
            "3. API 및 서비스 → 사용자 인증 정보\n"
            "4. 사용자 인증 정보 만들기 → OAuth 클라이언트 ID\n"
            "5. 애플리케이션 유형: 데스크톱 앱\n"
            "6. 만들기 → JSON 다운로드\n"
            "7. 아래 버튼으로 파일 선택"
        )
        steps.setStyleSheet("font-size: 12px; color: #3c4043; line-height: 1.6;")
        steps.setWordWrap(True)
        layout.addWidget(steps)

        open_console_btn = QPushButton("Google Cloud Console 열기 →")
        open_console_btn.setStyleSheet(self._link_btn_style())
        open_console_btn.clicked.connect(lambda: subprocess.run(
            ["open", "https://console.cloud.google.com/apis/credentials"], check=False
        ))
        layout.addWidget(open_console_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #e0e0e0;")
        layout.addWidget(sep)

        self._status = QLabel(f"저장 위치:\n{CREDENTIALS_FILE}")
        self._status.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

        select_btn = QPushButton("credentials.json 선택하기")
        select_btn.setStyleSheet(self._primary_btn_style())
        select_btn.clicked.connect(self._pick_file)
        layout.addWidget(select_btn)

        layout.addStretch()

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "credentials.json 선택", os.path.expanduser("~/Downloads"),
            "JSON 파일 (*.json)"
        )
        if not path:
            return
        try:
            OAuthFlow().set_credentials_file(path)
            self._status.setText("✅ credentials.json 저장 완료!\n로그인 화면으로 돌아갑니다.")
            self._status.setStyleSheet("font-size: 11px; color: #1e8e3e;")
            self.done.emit()
        except Exception as e:
            self._status.setText(f"❌ 오류: {e}")
            self._status.setStyleSheet("font-size: 11px; color: #ea4335;")

    def _primary_btn_style(self):
        return """
            QPushButton {
                background: #1a73e8; color: white;
                border: none; border-radius: 6px;
                padding: 9px; font-size: 13px;
            }
            QPushButton:hover { background: #1557b0; }
        """

    def _link_btn_style(self):
        return """
            QPushButton {
                background: transparent; color: #1a73e8;
                border: none; font-size: 12px; text-align: left;
                padding: 0;
            }
            QPushButton:hover { color: #1557b0; }
        """


# ── 메인 로그인 뷰 ─────────────────────────────────────────────────

class _LoginView(QWidget):
    go_setup = pyqtSignal()
    login_success = pyqtSignal()

    def __init__(self, client: KeepClient):
        super().__init__()
        self._client = client
        self._worker: _OAuthWorker | None = None
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

        layout.addSpacing(24)

        # Google 로그인 (주 버튼)
        self._oauth_btn = QPushButton("  Google로 로그인")
        self._oauth_btn.setStyleSheet("""
            QPushButton {
                background: #fff; color: #3c4043;
                border: 1px solid #dadce0; border-radius: 6px;
                padding: 10px; font-size: 14px; font-weight: 500;
            }
            QPushButton:hover { background: #f8f9fa; border-color: #c6c6c6; }
            QPushButton:disabled { color: #9aa0a6; }
        """)
        self._oauth_btn.clicked.connect(self._start_oauth)
        layout.addWidget(self._oauth_btn)

        # 상태 메시지
        self._status = QLabel()
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setStyleSheet("font-size: 12px; color: #5f6368;")
        self._status.setWordWrap(True)
        self._status.hide()
        layout.addWidget(self._status)

        # 구분선
        sep_layout = QVBoxLayout()
        sep_layout.setContentsMargins(0, 8, 0, 8)
        sep_lbl = QLabel("─── 또는 ───")
        sep_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sep_lbl.setStyleSheet("font-size: 11px; color: #9aa0a6;")
        sep_layout.addWidget(sep_lbl)
        layout.addLayout(sep_layout)

        # 앱 비밀번호 폼
        self._email = QLineEdit()
        self._email.setPlaceholderText("Google 이메일")
        self._email.setStyleSheet(self._input_style())
        layout.addWidget(self._email)

        self._password = QLineEdit()
        self._password.setPlaceholderText("앱 비밀번호 (16자리)")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setStyleSheet(self._input_style())
        self._password.returnPressed.connect(self._do_password_login)
        layout.addWidget(self._password)

        self._error_label = QLabel()
        self._error_label.setStyleSheet("color: #ea4335; font-size: 12px;")
        self._error_label.setWordWrap(True)
        self._error_label.hide()
        layout.addWidget(self._error_label)

        self._pw_btn = QPushButton("앱 비밀번호로 로그인")
        self._pw_btn.setStyleSheet("""
            QPushButton {
                background: #f1f3f4; color: #3c4043;
                border: none; border-radius: 6px;
                padding: 9px; font-size: 13px;
            }
            QPushButton:hover { background: #e8eaed; }
            QPushButton:disabled { color: #9aa0a6; }
        """)
        self._pw_btn.clicked.connect(self._do_password_login)
        layout.addWidget(self._pw_btn)

        layout.addStretch()

    # ── OAuth 플로우 ──────────────────────────────────────────

    def _start_oauth(self):
        if not OAuthFlow().has_credentials:
            self.go_setup.emit()
            return

        self._oauth_btn.setEnabled(False)
        self._oauth_btn.setText("  브라우저에서 로그인 중…")
        self._show_status("브라우저 창에서 Google 계정을 선택해주세요.")

        self._worker = _OAuthWorker()
        self._worker.success.connect(self._on_oauth_success)
        self._worker.error.connect(self._on_oauth_error)
        self._worker.start()

    def _on_oauth_success(self, email: str, token: str):
        try:
            self._client.login_with_oauth(email, token)
            self.login_success.emit()
        except AuthError as e:
            self._on_oauth_error(str(e))
        finally:
            self._reset_oauth_btn()

    def _on_oauth_error(self, msg: str):
        self._show_status(f"❌ {msg}", error=True)
        self._reset_oauth_btn()

    def _reset_oauth_btn(self):
        self._oauth_btn.setEnabled(True)
        self._oauth_btn.setText("  Google로 로그인")

    # ── 앱 비밀번호 플로우 ────────────────────────────────────

    def _do_password_login(self):
        email = self._email.text().strip()
        pw = self._password.text().strip()
        if not email or not pw:
            self._show_error("이메일과 비밀번호를 입력해주세요.")
            return

        self._pw_btn.setEnabled(False)
        self._pw_btn.setText("로그인 중…")
        self._error_label.hide()

        try:
            self._client.login(email, pw)
            self.login_success.emit()
        except AuthError as e:
            self._show_error(str(e))
        finally:
            self._pw_btn.setEnabled(True)
            self._pw_btn.setText("앱 비밀번호로 로그인")

    # ── 헬퍼 ─────────────────────────────────────────────────

    def _show_status(self, msg: str, error: bool = False):
        color = "#ea4335" if error else "#5f6368"
        self._status.setStyleSheet(f"font-size: 12px; color: {color};")
        self._status.setText(msg)
        self._status.show()

    def _show_error(self, msg: str):
        self._error_label.setText(msg)
        self._error_label.show()

    def _input_style(self) -> str:
        return """
            QLineEdit {
                border: 1px solid #dadce0; border-radius: 6px;
                padding: 8px 12px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #1a73e8; }
        """


# ── 퍼블릭 위젯 ──────────────────────────────────────────────────

class LoginWidget(QWidget):
    login_success = pyqtSignal()

    def __init__(self, client: KeepClient):
        super().__init__()
        self._stack = QStackedWidget(self)

        self._login_view = _LoginView(client)
        self._login_view.login_success.connect(self.login_success)
        self._login_view.go_setup.connect(lambda: self._stack.setCurrentIndex(1))

        self._setup_view = _SetupGuideWidget()
        self._setup_view.done.connect(lambda: self._stack.setCurrentIndex(0))

        self._stack.addWidget(self._login_view)   # 0
        self._stack.addWidget(self._setup_view)   # 1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)
