import sys
from PyQt6.QtWidgets import QApplication
from keep4mac.app import Keep4MacApp


def main():
    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)

    keep_app = Keep4MacApp(qt_app)
    keep_app.start()   # rumps.run() — 블로킹, 앱 종료까지 반환 안 함


if __name__ == "__main__":
    main()
