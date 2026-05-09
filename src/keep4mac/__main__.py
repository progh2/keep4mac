import sys
from PyQt6.QtWidgets import QApplication
from keep4mac.app import Keep4MacApp


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    keep_app = Keep4MacApp(app)
    keep_app.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
