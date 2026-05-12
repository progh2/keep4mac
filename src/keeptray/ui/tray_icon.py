import logging
import random

import rumps
from AppKit import NSColor, NSImage, NSImageSymbolConfiguration, NSObject, NSTrackingArea
from PyQt6.QtCore import QCoreApplication
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
_NSEventMaskRightMouseDown = 1 << 3   # = 8

_open_panel_fn = None
_btn_ref = None
_nsitem_ref = None
_default_image = None
_colored_images: list = []
_right_click_monitor = None


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


def _show_quit_menu():
    """트레이 버튼 위치에 Quit 메뉴를 팝업한다."""
    from AppKit import NSApplication, NSMenu, NSMenuItem
    menu = NSMenu.alloc().init()
    menu.setAutoenablesItems_(False)
    quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
        "Quit keeptray", "terminate:", ""
    )
    quit_item.setTarget_(NSApplication.sharedApplication())
    quit_item.setEnabled_(True)
    menu.addItem_(quit_item)
    if _nsitem_ref:
        _nsitem_ref.popUpStatusItemMenu_(menu)


def _setup_right_click_monitor():
    """글로벌 우클릭 이벤트 모니터 — 트레이 버튼 위에서 우클릭 시 Quit 메뉴."""
    global _right_click_monitor
    from AppKit import NSEvent, NSScreen

    def _handler(event):
        if _btn_ref is None:
            return
        btn_window = _btn_ref.window()
        if btn_window is None:
            return

        # 버튼의 AppKit 스크린 좌표 (좌하단 기준)
        btn_rect = btn_window.convertRectToScreen_(
            _btn_ref.convertRect_toView_(_btn_ref.bounds(), None)
        )

        # CGEvent 위치: Quartz 좌표 (주화면 좌상단 기준) → AppKit 좌표로 변환
        try:
            import Quartz
            cg_loc = Quartz.CGEventGetLocation(event.CGEvent())
        except Exception:
            return
        primary_h = NSScreen.screens()[0].frame().size.height
        click_x = cg_loc.x
        click_y = primary_h - cg_loc.y

        bx = btn_rect.origin.x
        by = btn_rect.origin.y
        bw = btn_rect.size.width
        bh = btn_rect.size.height

        if bx <= click_x <= bx + bw and by <= click_y <= by + bh:
            _show_quit_menu()

    _right_click_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
        _NSEventMaskRightMouseDown, _handler
    )
    logger.info("우클릭 글로벌 모니터 등록 완료")


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
        super().__init__(name="keeptray", title="🗒", quit_button=None)
        self._qt_app = qt_app
        self._click_setup_done = False

        self._client = KeepClient()
        if self._client.resume():
            logger.info("자동 로그인 성공")
            self._client.load_disk_cache()

        self._panel = MainPanel(self._client, quit_callback=self._quit_from_panel)

    # ── 직접 클릭 + 호버 색상 설정 ────────────────────────────

    @rumps.timer(0.3)
    def _setup_direct_click(self, _):
        if self._click_setup_done:
            return
        self._click_setup_done = True
        global _open_panel_fn, _btn_ref, _nsitem_ref
        try:
            _open_panel_fn = self._panel.toggle_visibility
            nsitem = self._nsapp.nsstatusitem
            _nsitem_ref = nsitem
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

            _setup_right_click_monitor()

            logger.info("트레이 클릭 + 호버 색상 설정 완료 (색상 수: %d)", len(_colored_images))
            self._panel.show_near_menubar()
        except Exception as e:
            logger.warning("설정 실패: %s", e, exc_info=True)

    # ── Qt 이벤트 루프 통합 ───────────────────────────────────

    @rumps.timer(0.05)
    def _process_qt(self, _):
        QCoreApplication.processEvents()

    def _quit_from_panel(self):
        rumps.quit_application()
