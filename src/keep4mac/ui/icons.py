from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap


def make_tray_icon(dark: bool = False) -> QIcon:
    """메뉴바용 트레이 아이콘 생성 (22x22)."""
    size = 22
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    fg = QColor("#FFFFFF") if dark else QColor("#000000")

    # 전구 몸통 (원)
    painter.setBrush(fg)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(3, 2, 16, 14)

    # 전구 아래 받침 (사각형)
    painter.drawRoundedRect(7, 15, 8, 3, 1, 1)
    painter.drawRoundedRect(8, 18, 6, 2, 1, 1)

    painter.end()
    return QIcon(pixmap)


def make_status_icon(state: str) -> QIcon:
    """상태별 아이콘: 'normal' | 'syncing' | 'error'."""
    size = 22
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    color_map = {"normal": "#000000", "syncing": "#4285F4", "error": "#EA4335"}
    fg = QColor(color_map.get(state, "#000000"))

    painter.setBrush(fg)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(3, 2, 16, 14)
    painter.drawRoundedRect(7, 15, 8, 3, 1, 1)
    painter.drawRoundedRect(8, 18, 6, 2, 1, 1)

    painter.end()
    return QIcon(pixmap)
