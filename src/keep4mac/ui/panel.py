import sys
from typing import Callable

from PyQt6.QtCore import Qt, QPoint, QRectF, QTimer, QUrl, pyqtSignal
from PyQt6.QtGui import QColor, QDesktopServices, QPainter, QPainterPath, QPen, QScreen
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from keep4mac.api.keep_client import KeepClient
from keep4mac.core import settings
import keep4mac.i18n as i18n
from keep4mac.ui.about_dialog import AboutDialog
from keep4mac.ui.login_widget import LoginWidget
from keep4mac.ui.note_editor_widget import NoteEditorWidget
from keep4mac.ui.note_list_widget import NoteListWidget
from keep4mac.ui.sidebar_widget import SidebarWidget

_IDX_LOGIN = 0
_IDX_NOTES = 1
_IDX_EDITOR = 2


class _DragBar(QWidget):
    """드래그로 패널을 이동하고 ✕ 버튼으로 닫는 28px 상단 바."""

    close_clicked = pyqtSignal()
    _HEIGHT = 28

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self._HEIGHT)
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setStyleSheet("background: #f5f5f7; border-bottom: 1px solid #e0e0e0;")
        self._drag_pos: QPoint | None = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(0)

        handle = QLabel("⠿")
        handle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        handle.setStyleSheet("color: #c0c0c0; font-size: 13px; background: transparent;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #aaaaaa;
                border: none;
                font-size: 10px;
                border-radius: 9px;
            }
            QPushButton:hover {
                background: #ff5f5f;
                color: white;
            }
        """)
        close_btn.clicked.connect(self.close_clicked)

        layout.addStretch(1)
        layout.addWidget(handle)
        layout.addStretch(1)
        layout.addWidget(close_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)


class MainPanel(QWidget):
    _RADIUS = 12.0
    _DRAG_H = _DragBar._HEIGHT

    def __init__(self, client: KeepClient, quit_callback: Callable | None = None):
        super().__init__(
            flags=Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._client = client
        self._quit_callback = quit_callback
        self.setFixedSize(420, 580 + self._DRAG_H)
        self._build_ui()
        self.setStyleSheet("QWidget#MainPanel { background: transparent; }")
        self.setObjectName("MainPanel")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 드래그 바
        self._drag_bar = _DragBar()
        self._drag_bar.close_clicked.connect(self.hide)
        root.addWidget(self._drag_bar)

        # 콘텐츠 행: 사이드바 + 스택
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self._sidebar = SidebarWidget()
        self._sidebar.new_note_requested.connect(self._on_new_note)
        self._sidebar.sync_requested.connect(self._on_sync)
        self._sidebar.open_web_requested.connect(self._on_open_web)
        self._sidebar.about_requested.connect(self._on_about)
        self._sidebar.logout_requested.connect(self._on_logout)
        self._sidebar.quit_requested.connect(self._on_quit)
        self._sidebar.lang_changed.connect(self._on_lang_changed)
        self._sidebar.hide()
        row.addWidget(self._sidebar)

        # 콘텐츠 스택 — WA_TranslucentBackground 환경에서 페이지 전환 시 잔상 방지
        self._stack = QStackedWidget()
        self._stack.setAutoFillBackground(True)
        self._stack.setStyleSheet("QStackedWidget { background: #ffffff; }")

        self._login_w = LoginWidget(self._client)
        self._login_w.login_success.connect(self._on_login_success)

        self._notes_w = NoteListWidget(self._client)
        self._notes_w.note_selected.connect(self._on_note_selected)

        self._editor_w = NoteEditorWidget(self._client)
        self._editor_w.back_requested.connect(self._on_editor_back)

        self._stack.addWidget(self._login_w)   # index 0
        self._stack.addWidget(self._notes_w)   # index 1
        self._stack.addWidget(self._editor_w)  # index 2

        row.addWidget(self._stack, 1)
        root.addLayout(row, 1)

    # ── 렌더링 ───────────────────────────────────────────────

    def paintEvent(self, event):
        """둥근 흰색 배경과 테두리를 직접 그린다 (Qt stylesheet border-radius는 실제 클리핑 안 함)."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        path = QPainterPath()
        path.addRoundedRect(rect, self._RADIUS, self._RADIUS)
        painter.fillPath(path, QColor("#ffffff"))
        painter.setPen(QPen(QColor("#d0d0d0"), 1))
        painter.drawPath(path)

    def showEvent(self, event):
        """CALayer로 자식 위젯까지 둥글게 클리핑하고 그림자를 추가한다 (macOS 전용)."""
        super().showEvent(event)
        if sys.platform != "darwin":
            return
        try:
            import ctypes
            import objc
            ns_view = objc.objc_object(c_void_p=ctypes.c_void_p(int(self.winId())))
            ns_view.setWantsLayer_(True)
            layer = ns_view.layer()
            layer.setCornerRadius_(self._RADIUS)
            layer.setMasksToBounds_(True)
            ns_win = ns_view.window()
            if ns_win is not None:
                ns_win.setHasShadow_(True)
                ns_win.setHidesOnDeactivate_(False)
        except Exception:
            pass

    def hideEvent(self, event):
        """패널이 숨겨질 때 현재 위치를 저장한다."""
        super().hideEvent(event)
        settings.set_window_pos(self.x(), self.y())

    # ── 표시 ─────────────────────────────────────────────────

    def show_near_menubar(self):
        pos = settings.get_window_pos()
        if pos:
            self.move(pos[0], pos[1])
        else:
            screen: QScreen = QApplication.primaryScreen()
            sg = screen.availableGeometry()
            x = sg.right() - self.width() - 8
            y = sg.top() + 4
            self.move(x, y)

        if self._client.is_logged_in:
            if self._stack.currentIndex() == _IDX_EDITOR:
                self._editor_w.auto_save_if_needed()
            self._show_notes()
        else:
            self._sidebar.hide()
            self._stack.setCurrentIndex(_IDX_LOGIN)

        self.show()
        self.raise_()
        self.activateWindow()

    def toggle_visibility(self):
        """트레이 아이콘 클릭 시 패널을 열거나 닫는다."""
        if self.isVisible():
            self.hide()
        else:
            self.show_near_menubar()

    def _show_notes(self):
        self._sidebar.show()
        self._stack.setCurrentIndex(_IDX_NOTES)
        self._notes_w.load_notes()

    # ── 슬롯 ─────────────────────────────────────────────────

    def _on_login_success(self):
        self._show_notes()

    def _on_note_selected(self, note_id: str):
        self._editor_w.load_note(note_id)
        self._stack.setCurrentIndex(_IDX_EDITOR)

    def _on_new_note(self):
        self._editor_w.new_note()
        self._stack.setCurrentIndex(_IDX_EDITOR)

    def _on_editor_back(self):
        self._show_notes()

    def _on_sync(self):
        self._notes_w.load_notes(force_sync=True)

    def _on_open_web(self):
        QDesktopServices.openUrl(QUrl("https://keep.google.com"))

    def _on_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def _on_logout(self):
        self._client.logout()
        self._sidebar.hide()
        self._stack.setCurrentIndex(_IDX_LOGIN)

    def _on_lang_changed(self, lang: str):
        i18n.setup()
        self._sidebar.retranslate_ui()
        self._notes_w.retranslate_ui()
        self._editor_w.retranslate_ui()
        lang_name = i18n.SUPPORTED_LANGS.get(lang, lang)
        msg = (
            f"{lang_name}(으)로 변경됐습니다."
            if lang == "ko" else
            f"Language changed to {lang_name}."
        )
        self._show_toast(msg)

    def _show_toast(self, message: str):
        toast = QLabel(message, self)
        toast.setWordWrap(True)
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toast.setStyleSheet("""
            QLabel {
                background: rgba(32,33,36,0.88);
                color: white;
                font-size: 12px;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        toast.adjustSize()
        toast.setFixedWidth(min(toast.sizeHint().width() + 24, self.width() - 32))
        toast.move(
            (self.width() - toast.width()) // 2,
            self.height() - toast.height() - 16,
        )
        toast.show()
        toast.raise_()
        QTimer.singleShot(3000, toast.deleteLater)

    def _on_quit(self):
        self.hide()
        if self._quit_callback:
            self._quit_callback()

    # ── 키 처리 ──────────────────────────────────────────────

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)
