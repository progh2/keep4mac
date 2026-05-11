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
    browsers_dir = base / "keep4mac" / "ms-playwright"
    browsers_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_dir)


def main():
    # 영구 브라우저 경로를 가장 먼저 설정 (PyInstaller 임시 경로 방지)
    _setup_playwright_browsers_path()

    import keep4mac.i18n as i18n
    from PyQt6.QtWidgets import QApplication, QDialog
    from keep4mac.app import Keep4MacApp

    i18n.setup()
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)

    # Playwright Chromium 미설치 시 자동 다운로드
    from keep4mac.ui.setup_dialog import chromium_installed, SetupDialog
    if not chromium_installed():
        dlg = SetupDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted:
            sys.exit(0)

    keep_app = Keep4MacApp(qt_app)
    keep_app.start()


if __name__ == "__main__":
    main()
