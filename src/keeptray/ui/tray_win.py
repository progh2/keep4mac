"""Windows 시스템 트레이 구현 — pystray + Qt 이벤트 루프 통합."""
import logging
import queue

import pystray
from PIL import Image, ImageDraw
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from keeptray.api.keep_client import KeepClient
from keeptray.ui.panel import MainPanel

logger = logging.getLogger(__name__)

_ICON_SIZE = 64
_ICON_BG = (26, 115, 232, 255)   # Google Keep 파란색


def _make_icon_image() -> Image.Image:
    """64×64 RGBA 트레이 아이콘을 생성한다."""
    img = Image.new("RGBA", (_ICON_SIZE, _ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 파란 원 배경
    margin = 4
    draw.ellipse(
        [margin, margin, _ICON_SIZE - margin, _ICON_SIZE - margin],
        fill=_ICON_BG,
    )
    # 노트 심볼: 흰 가로줄 3개
    line_color = (255, 255, 255, 255)
    lw = 3
    x0, x1 = 16, _ICON_SIZE - 16
    for y in (22, 32, 42):
        draw.rectangle([x0, y - lw // 2, x1, y + lw // 2], fill=line_color)
    return img


class WindowsTray:
    """pystray 기반 Windows 시스템 트레이 앱.

    pystray 콜백은 백그라운드 스레드에서 실행되므로, Qt UI 조작은
    SimpleQueue + QTimer(50ms)를 통해 메인 스레드로 전달한다.
    """

    def __init__(self, qt_app: QApplication, panel: MainPanel, client: KeepClient):
        self._qt_app = qt_app
        self._panel = panel
        self._client = client
        self._icon: pystray.Icon | None = None
        self._q: queue.SimpleQueue = queue.SimpleQueue()

        # 메인 스레드 drain 타이머
        self._drain_timer = QTimer()
        self._drain_timer.timeout.connect(self._drain_queue)

    def start(self):
        """트레이를 백그라운드 스레드에서 시작하고 drain 타이머를 활성화한다."""
        menu = pystray.Menu(
            pystray.MenuItem("keeptray", self._on_toggle, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("위치 초기화", self._on_reset_position),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("종료", self._on_quit),
        )
        self._icon = pystray.Icon(
            "keeptray",
            _make_icon_image(),
            "keeptray",
            menu,
        )
        self._icon.run_detached()
        self._drain_timer.start(50)
        QTimer.singleShot(500, self._panel.show_near_menubar)
        logger.info("Windows 트레이 시작 완료")

    # ── 콜백 (백그라운드 스레드에서 호출) ────────────────────────

    def _on_toggle(self, icon, item):
        self._q.put(self._panel.toggle_visibility)

    def _on_reset_position(self, icon, item):
        self._q.put(self._panel.reset_position)

    def _on_quit(self, icon, item):
        def _do_quit():
            if self._icon:
                self._icon.stop()
            self._qt_app.quit()
        self._q.put(_do_quit)

    # ── drain (메인 스레드에서 실행) ─────────────────────────────

    def _drain_queue(self):
        while True:
            try:
                fn = self._q.get_nowait()
                fn()
            except queue.Empty:
                break
