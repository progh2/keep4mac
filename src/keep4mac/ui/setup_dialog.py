"""Playwright Chromium 자동 설치 다이얼로그."""
import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout,
)


def chromium_installed() -> bool:
    """Playwright Chromium 바이너리가 존재하는지 확인한다."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            exe = p.chromium.executable_path
        return Path(exe).exists()
    except Exception:
        return False


def _install_command() -> tuple[list[str], dict | None]:
    """playwright install chromium 실행 인자와 환경변수를 반환한다."""
    if getattr(sys, "frozen", False):
        from playwright._impl._driver import get_driver_env
        try:
            # Playwright ≥1.45: compute_driver_executable() → (node_exe, cli_js)
            from playwright._impl._driver import compute_driver_executable
            node_exe, cli_js = compute_driver_executable()
            return [node_exe, cli_js, "install", "chromium"], get_driver_env()
        except ImportError:
            # Playwright <1.45: get_driver_executable() → driver_path string
            from playwright._impl._driver import get_driver_executable
            return [get_driver_executable(), "install", "chromium"], get_driver_env()
    else:
        return [sys.executable, "-m", "playwright", "install", "chromium"], None


class _InstallThread(QThread):
    done = pyqtSignal()
    error = pyqtSignal(str)
    output = pyqtSignal(str)

    def run(self):
        try:
            cmd, env = _install_command()
            kwargs = dict(
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if env:
                kwargs["env"] = env
            proc = subprocess.Popen(cmd, **kwargs)
            for line in proc.stdout:
                line = line.strip()
                if line:
                    self.output.emit(line)
            proc.wait()
            if proc.returncode == 0:
                self.done.emit()
            else:
                self.error.emit(f"설치 실패 (종료 코드: {proc.returncode})")
        except Exception as e:
            self.error.emit(str(e))


class SetupDialog(QDialog):
    """Chromium 미설치 시 자동 다운로드 진행 창."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("keep4mac — 초기 설정")
        self.setFixedWidth(400)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )
        self._thread: _InstallThread | None = None
        self._build_ui()
        self._start_install()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        self._title_lbl = QLabel("Chromium 브라우저 다운로드 중…")
        self._title_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #1c1c1e;"
        )
        layout.addWidget(self._title_lbl)

        self._desc_lbl = QLabel(
            "Google 로그인에 필요한 브라우저를 설치합니다.\n"
            "완료 후 자동으로 앱이 시작됩니다."
        )
        self._desc_lbl.setStyleSheet("font-size: 12px; color: #636366;")
        self._desc_lbl.setWordWrap(True)
        layout.addWidget(self._desc_lbl)

        layout.addSpacing(4)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)   # 불확정 모드
        self._progress.setFixedHeight(6)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 3px;
                background: #e5e5ea;
            }
            QProgressBar::chunk {
                background: #007AFF;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self._progress)

        self._status_lbl = QLabel("준비 중…")
        self._status_lbl.setStyleSheet("font-size: 11px; color: #8e8e93;")
        layout.addWidget(self._status_lbl)

        # 에러 시 표시되는 버튼 행 (평소엔 숨김)
        self._btn_row = QHBoxLayout()
        self._btn_row.addStretch()

        self._retry_btn = QPushButton("다시 시도")
        self._retry_btn.setFixedHeight(28)
        self._retry_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF; color: white;
                border: none; border-radius: 6px;
                font-size: 12px; padding: 0 16px;
            }
            QPushButton:hover { background: #0066d6; }
        """)
        self._retry_btn.clicked.connect(self._on_retry)
        self._retry_btn.hide()
        self._btn_row.addWidget(self._retry_btn)

        self._quit_btn = QPushButton("종료")
        self._quit_btn.setFixedHeight(28)
        self._quit_btn.setStyleSheet("""
            QPushButton {
                background: transparent; color: #636366;
                border: 1px solid #d1d1d6; border-radius: 6px;
                font-size: 12px; padding: 0 16px;
            }
            QPushButton:hover { background: #f2f2f7; }
        """)
        self._quit_btn.clicked.connect(self.reject)
        self._quit_btn.hide()
        self._btn_row.addWidget(self._quit_btn)

        layout.addLayout(self._btn_row)
        self.adjustSize()

    def _start_install(self):
        self._thread = _InstallThread()
        self._thread.done.connect(self._on_done)
        self._thread.error.connect(self._on_error)
        self._thread.output.connect(self._on_output)
        self._thread.start()

    def _on_output(self, line: str):
        self._status_lbl.setText(line[:70])

    def _on_done(self):
        self._status_lbl.setText("설치 완료!")
        self.accept()

    def _on_error(self, msg: str):
        self._progress.setRange(0, 1)
        self._progress.setValue(0)
        self._title_lbl.setText("설치 실패")
        self._title_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #FF3B30;"
        )
        self._status_lbl.setText(msg[:80])
        self._retry_btn.show()
        self._quit_btn.show()
        self.adjustSize()

    def _on_retry(self):
        self._retry_btn.hide()
        self._quit_btn.hide()
        self._progress.setRange(0, 0)
        self._title_lbl.setText("Chromium 브라우저 다운로드 중…")
        self._title_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 600; color: #1c1c1e;"
        )
        self._status_lbl.setText("준비 중…")
        self.adjustSize()
        self._start_install()
