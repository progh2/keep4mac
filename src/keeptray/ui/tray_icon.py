import logging
import random

import rumps
from AppKit import NSColor, NSImage, NSImageSymbolConfiguration, NSObject, NSTrackingArea
from PyQt6.QtCore import QCoreApplication, QTimer
from PyQt6.QtWidgets import QApplication

from keeptray.api.keep_client import KeepClient
from keeptray.ui.panel import MainPanel

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


class _MenuDelegate(NSObject):
    """
    좌클릭: 메뉴를 즉시 취소하고 패널 토글.
    우클릭 / Ctrl+클릭: Quit 메뉴를 그대로 표시.
    """
    def menuWillOpen_(self, menu):
        from AppKit import NSApplication
        event = NSApplication.sharedApplication().currentEvent()
        # NSEventTypeLeftMouseDown = 1
        if event and int(event.type()) == 1:
            menu.cancelTrackingWithoutAnimation()
            if _open_panel_fn:
                QTimer.singleShot(0, _open_panel_fn)


class _HoverTarget(NSObject):
    """트래킹 영역 호버 색상 처리 전용."""
    def mouseEntered_(self, event):
        if _btn_ref is not None and _colored_images:
            _btn_ref.setImage_(random.choice(_colored_images))

    def mouseExited_(self, event):
        if _btn_ref is not None and _default_image is not None:
            _btn_ref.setImage_(_default_image)


class TrayApp(rumps.App):
    def __init__(self, qt_app: QApplication):
        super().__init__(name="keeptray", title="🗒", quit_button=None)
        self._qt_app = qt_app
        self._click_setup_done = False

        self._client = KeepClient()
        if self._client.resume():
            logger.info("자동 로그인 성공")
            self._client.load_disk_cache()

        self._panel = MainPanel(self._client, quit_callback=self._quit_from_panel)

    # ── 클릭 + 호버 색상 설정 ─────────────────────────────────

    @rumps.timer(0.3)
    def _setup_direct_click(self, _):
        if self._click_setup_done:
            return
        self._click_setup_done = True
        global _open_panel_fn, _btn_ref
        try:
            from AppKit import NSApplication, NSMenu, NSMenuItem

            _open_panel_fn = self._panel.toggle_visibility
            nsitem = self._nsapp.nsstatusitem
            btn = nsitem.button()
            _btn_ref = btn

            _build_colored_images()
            if _default_image is not None:
                btn.setImage_(_default_image)
                btn.setTitle_("")

            # Quit 메뉴 생성
            menu = NSMenu.alloc().init()
            menu.setAutoenablesItems_(False)
            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                "Quit keeptray", "terminate:", ""
            )
            quit_item.setTarget_(NSApplication.sharedApplication())
            quit_item.setEnabled_(True)
            menu.addItem_(quit_item)

            # 좌클릭은 패널 토글, 우클릭/Ctrl+클릭은 메뉴 표시
            self._menu_delegate = _MenuDelegate.alloc().init()
            menu.setDelegate_(self._menu_delegate)
            nsitem.setMenu_(menu)

            # 호버 색상용 트래킹 영역
            self._hover_target = _HoverTarget.alloc().init()
            tracking_area = NSTrackingArea.alloc().initWithRect_options_owner_userInfo_(
                btn.bounds(),
                _NSTrackingMouseEnteredAndExited | _NSTrackingActiveAlways,
                self._hover_target,
                None,
            )
            btn.addTrackingArea_(tracking_area)

            logger.info("트레이 설정 완료 (색상 수: %d)", len(_colored_images))
            self._panel.show_near_menubar()
        except Exception as e:
            logger.warning("설정 실패: %s", e, exc_info=True)

    # ── Qt 이벤트 루프 통합 ───────────────────────────────────

    @rumps.timer(0.05)
    def _process_qt(self, _):
        QCoreApplication.processEvents()

    def _quit_from_panel(self):
        rumps.quit_application()
