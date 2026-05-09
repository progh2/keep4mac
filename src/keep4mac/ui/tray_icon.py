import logging
import random

import rumps
from AppKit import NSColor, NSImage, NSImageSymbolConfiguration, NSObject, NSTrackingArea
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtWidgets import QApplication

from keep4mac.api.keep_client import KeepClient
from keep4mac.ui.panel import MainPanel

logger = logging.getLogger(__name__)

_SF_SYMBOL = "note.text"

# Google Keep 노트 팔레트 (RGB 0–1)
_PALETTE_RGB = [
    (0.95, 0.27, 0.27),  # Red
    (0.98, 0.74, 0.02),  # Orange
    (0.99, 0.90, 0.20),  # Yellow
    (0.26, 0.70, 0.33),  # Green
    (0.00, 0.59, 0.53),  # Teal
    (0.13, 0.59, 0.95),  # Blue
    (0.01, 0.66, 0.96),  # Cerulean
    (0.61, 0.15, 0.69),  # Purple
    (0.91, 0.12, 0.39),  # Pink
    (0.62, 0.42, 0.28),  # Brown
]

_NSTrackingMouseEnteredAndExited = 0x01
_NSTrackingActiveAlways = 0x80

_open_panel_fn = None
_btn_ref = None
_default_image = None
_colored_images: list = []


def _build_colored_images():
    """기동 시 팔레트 10색 NSImage를 미리 생성해둔다."""
    global _default_image, _colored_images
    base = NSImage.imageWithSystemSymbolName_accessibilityDescription_(_SF_SYMBOL, None)
    if base is None:
        return
    _default_image = base
    for r, g, b in _PALETTE_RGB:
        color = NSColor.colorWithSRGBRed_green_blue_alpha_(r, g, b, 1.0)
        cfg = NSImageSymbolConfiguration.configurationWithHierarchicalColor_(color)
        _colored_images.append(base.imageWithSymbolConfiguration_(cfg))


class _ClickTarget(NSObject):
    def openPanel_(self, sender):
        if _open_panel_fn:
            _open_panel_fn()

    def mouseEntered_(self, event):
        if _btn_ref is not None and _colored_images:
            _btn_ref.setImage_(random.choice(_colored_images))

    def mouseExited_(self, event):
        if _btn_ref is not None and _default_image is not None:
            _btn_ref.setImage_(_default_image)


class TrayApp(rumps.App):
    def __init__(self, qt_app: QApplication):
        super().__init__(name="keep4mac", title="🗒", quit_button=None)
        self._qt_app = qt_app
        self._click_setup_done = False

        self._client = KeepClient()
        if self._client.resume():
            logger.info("자동 로그인 성공")

        self._panel = MainPanel(self._client, quit_callback=self._quit_from_panel)

    # ── 직접 클릭 + 호버 색상 설정 ────────────────────────────

    @rumps.timer(0.3)
    def _setup_direct_click(self, _):
        if self._click_setup_done:
            return
        self._click_setup_done = True
        global _open_panel_fn, _btn_ref
        try:
            _open_panel_fn = self._panel.show_near_menubar
            nsitem = self._nsapp.nsstatusitem
            nsitem.setMenu_(None)
            btn = nsitem.button()
            _btn_ref = btn

            _build_colored_images()
            if _default_image is not None:
                btn.setImage_(_default_image)
                btn.setTitle_("")

            self._click_target = _ClickTarget.alloc().init()
            btn.setTarget_(self._click_target)
            btn.setAction_("openPanel:")

            tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                btn.bounds(),
                _NSTrackingMouseEnteredAndExited | _NSTrackingActiveAlways,
                self._click_target,
                None,
            )
            btn.addTrackingArea_(tracking_area)
            logger.info("트레이 클릭 + 호버 색상 설정 완료 (색상 수: %d)", len(_colored_images))
        except Exception as e:
            logger.warning("설정 실패: %s", e, exc_info=True)

    # ── Qt 이벤트 루프 통합 ───────────────────────────────────

    @rumps.timer(0.05)
    def _process_qt(self, _):
        QCoreApplication.processEvents()

    def _quit_from_panel(self):
        rumps.quit_application()
