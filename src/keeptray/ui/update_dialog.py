"""업데이트 확인·다운로드·설치 다이얼로그."""
import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QDialogButtonBox, QLabel, QProgressBar,
    QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QHBoxLayout,
)

from keeptray.core import updater as _up
from keeptray.i18n import gettext as _

logger = logging.getLogger(__name__)

_DLG_CSS = """
    QDialog  { background: #ffffff; color: #1c1c1e; }
    QLabel   { color: #1c1c1e; }
    QTextEdit { background: #f9f9fb; border: 1px solid #d1d1d6;
                border-radius: 6px; font-size: 12px; color: #1c1c1e; }
    QProgressBar {
        border: none; border-radius: 3px; background: #e5e5ea; height: 6px;
    }
    QProgressBar::chunk { background: #007AFF; border-radius: 3px; }
"""


class _CheckThread(QThread):
    found = pyqtSignal(dict)
    not_found = pyqtSignal()

    def run(self):
        info = _up.check_update()
        if info:
            self.found.emit(info)
        else:
            self.not_found.emit()


class _DownloadThread(QThread):
    progress = pyqtSignal(int, int)   # (downloaded, total)
    done = pyqtSignal(str)            # temp file path
    error = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        try:
            path = _up.download(self._url, progress_cb=lambda d, t: self.progress.emit(d, t))
            self.done.emit(str(path))
        except Exception as e:
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    """업데이트 진행 상태를 보여주는 다이얼로그."""
    install_ready = pyqtSignal(str)  # 설치 완료 시 temp path 전달

    def __init__(self, release_info: dict, parent=None):
        super().__init__(parent)
        self._info = release_info
        self._asset = _up.get_asset(release_info["assets"])
        self._dl_thread: _DownloadThread | None = None
        self.setWindowTitle(_("Update Available"))
        self.setMinimumWidth(420)
        self.setStyleSheet(_DLG_CSS)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        # 버전 제목
        ver = self._info["version"]
        title = QLabel(f"🎉  keeptray {ver} {_('is available!')}")
        title.setStyleSheet("font-size: 15px; font-weight: 600; color: #1c1c1e;")
        layout.addWidget(title)

        current = _up.current_version()
        sub = QLabel(f"{_('Current version')}: v{current}  →  {ver}")
        sub.setStyleSheet("font-size: 12px; color: #636366;")
        layout.addWidget(sub)

        # 릴리즈 노트
        notes = self._info.get("notes", "")
        if notes:
            notes_lbl = QLabel(_("Release notes:"))
            notes_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1c1c1e;")
            layout.addWidget(notes_lbl)

            notes_edit = QTextEdit()
            notes_edit.setReadOnly(True)
            notes_edit.setPlainText(notes)
            notes_edit.setFixedHeight(100)
            layout.addWidget(notes_edit)

        # 진행 바 (숨김 상태로 시작)
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.hide()
        layout.addWidget(self._progress)

        self._status_lbl = QLabel("")
        self._status_lbl.setStyleSheet("font-size: 11px; color: #636366;")
        self._status_lbl.hide()
        layout.addWidget(self._status_lbl)

        # 버튼 행
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._later_btn = QPushButton(_("Later"))
        self._later_btn.setStyleSheet(
            "QPushButton { background: transparent; color: #636366;"
            "border: 1px solid #d1d1d6; border-radius: 6px; font-size: 13px; padding: 6px 16px; }"
            "QPushButton:hover { background: #f2f2f7; }"
        )
        self._later_btn.clicked.connect(self.reject)
        btn_row.addWidget(self._later_btn)

        self._update_btn = QPushButton(f"⬇  {_('Update Now')}")
        self._update_btn.setStyleSheet(
            "QPushButton { background: #007AFF; color: white;"
            "border: none; border-radius: 6px; font-size: 13px; padding: 6px 16px; }"
            "QPushButton:hover { background: #0066d6; }"
            "QPushButton:disabled { background: #a0c4ff; }"
        )
        self._update_btn.clicked.connect(self._start_download)
        if not self._asset:
            self._update_btn.setEnabled(False)
            self._update_btn.setToolTip(_("No asset for this platform"))
        btn_row.addWidget(self._update_btn)

        layout.addLayout(btn_row)

    def _start_download(self):
        self._update_btn.setEnabled(False)
        self._later_btn.setEnabled(False)
        self._progress.show()
        self._status_lbl.show()
        self._status_lbl.setText(_("Downloading…"))

        url = self._asset["browser_download_url"]
        size_mb = self._asset.get("size", 0) / 1024 / 1024
        logger.info("업데이트 다운로드 시작: %s (%.1f MB)", url, size_mb)

        self._dl_thread = _DownloadThread(url)
        self._dl_thread.progress.connect(self._on_progress)
        self._dl_thread.done.connect(self._on_done)
        self._dl_thread.error.connect(self._on_error)
        self._dl_thread.start()

    def _on_progress(self, done: int, total: int):
        pct = int(done * 100 / total)
        self._progress.setValue(pct)
        mb_done = done / 1024 / 1024
        mb_total = total / 1024 / 1024
        self._status_lbl.setText(f"{_('Downloading…')}  {mb_done:.1f} / {mb_total:.1f} MB")

    def _on_done(self, path: str):
        self._progress.setValue(100)
        self._status_lbl.setText(_("Installing…"))
        self.install_ready.emit(path)

    def _on_error(self, msg: str):
        self._status_lbl.setText(f"❌  {msg}")
        self._status_lbl.setStyleSheet("font-size: 11px; color: #FF3B30;")
        self._update_btn.setEnabled(True)
        self._later_btn.setEnabled(True)
        logger.warning("업데이트 다운로드 실패: %s", msg)
