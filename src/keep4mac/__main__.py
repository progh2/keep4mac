import sys
from PyQt6.QtWidgets import QApplication, QDialog
import keep4mac.i18n as i18n
from keep4mac.app import Keep4MacApp


def main():
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
