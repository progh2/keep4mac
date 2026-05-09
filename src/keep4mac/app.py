from PyQt6.QtWidgets import QApplication


class Keep4MacApp:
    def __init__(self, qt_app: QApplication):
        self.qt_app = qt_app

    def start(self):
        # Phase 3에서 트레이 아이콘 초기화
        # Phase 4에서 메인 패널 초기화
        print("keep4mac started")
