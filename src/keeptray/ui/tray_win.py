"""Windows 시스템 트레이 구현 — pystray + Qt 이벤트 루프 통합."""
import logging
import queue

import pystray
from PIL import Image, ImageDraw
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from keeptray.api.keep_client import KeepClient
from keeptray.i18n import gettext as _
from keeptray.ui.panel import MainPanel

logger = logging.getLogger(__name__)

_ICON_SIZE = 64
_ICON_BG = (251, 188, 4, 255)    # Google Keep 노란색
_ICON_FG = (255, 255, 255, 255)  # 흰색 전구


def _make_icon_image() -> Image.Image:
    """64×64 RGBA 트레이 아이콘 (노란 배경 + 흰 전구, 설치 아이콘과 동일 디자인)."""
    s = _ICON_SIZE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 노란 배경 - 둥근 사각형
    pad = max(1, int(s * 0.04))
    draw.rounded_rectangle([pad, pad, s - pad, s - pad],
                           radius=int(s * 0.22), fill=_ICON_BG)

    # 전구 몸통 (원)
    cx, cy = s / 2, s * 0.40
    bulb_r = s * 0.20
    draw.ellipse([cx - bulb_r, cy - bulb_r, cx + bulb_r, cy + bulb_r], fill=_ICON_FG)

    # 전구 받침 1단
    bw = s * 0.16
    bh1 = s * 0.07
    bx0 = cx - bw / 2
    by0 = cy + bulb_r - s * 0.015
    draw.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh1],
                           radius=max(1, int(s * 0.015)), fill=_ICON_FG)

    # 전구 받침 2단
    bw2 = bw * 0.72
    bx2 = cx - bw2 / 2
    by2 = by0 + bh1
    draw.rounded_rectangle([bx2, by2, bx2 + bw2, by2 + s * 0.05],
                           radius=max(1, int(s * 0.015)), fill=_ICON_FG)

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
            pystray.MenuItem(lambda item: _("Reset Position"), self._on_reset_position),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lambda item: _("Quit keeptray"), self._on_quit),
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
