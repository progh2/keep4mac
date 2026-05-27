import os
import sys
from pathlib import Path


def _setup_playwright_browsers_path() -> None:
    """PyInstaller 번들에서 Playwright 브라우저를 영구 위치에 저장하도록 강제 설정."""
    if "PLAYWRIGHT_BROWSERS_PATH" in os.environ:
        return
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    browsers_dir = base / "keeptray" / "ms-playwright"
    browsers_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)


def _setup_error_log() -> None:
    """Windows frozen 앱에서 미처리 예외를 파일에 기록한다."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    import logging
    log_dir = Path(os.environ.get("APPDATA", Path.home())) / "keeptray"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "error.log"
    logging.basicConfig(
        filename=str(log_path),
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )

    def _excepthook(exc_type, exc_value, exc_tb):
        import traceback
        logging.critical(
            "Unhandled exception:\n%s",
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )
    sys.excepthook = _excepthook


def main():
    # Windows frozen 앱 에러 로그 설정 (가장 먼저)
    _setup_error_log()

    # 영구 브라우저 경로를 가장 먼저 설정 (PyInstaller 임시 경로 방지)
    _setup_playwright_browsers_path()

    import keeptray.i18n as i18n
    from PyQt6.QtWidgets import QApplication, QDialog
    from keeptray.app import KeepTrayApp

    i18n.setup()
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)

    # Playwright Chromium 미설치 시 자동 다운로드
    from keeptray.ui.setup_dialog import chromium_installed, SetupDialog
    if not chromium_installed():
        dlg = SetupDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)

    keep_app = KeepTrayApp(qt_app)
    keep_app.start()


if __name__ == "__main__":
    main()
