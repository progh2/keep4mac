import logging
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROFILE_DIR = Path.home() / ".config" / "keep4mac" / "chrome_profile"

_GOOGLE_COOKIE_NAMES = {
    "SID", "SSID", "APISID", "SAPISID", "HSID",
    "OSID", "LSID", "NID", "1P_JAR",
    "__Secure-1PSID", "__Secure-3PSID",
    "__Secure-1PAPISID", "__Secure-3PAPISID",
    "__Secure-1PSIDTS", "__Secure-3PSIDTS",
}

_KEEP_API_HOST = "notes-pa.clients6.google.com/notes/v1"


def run_browser_login() -> tuple[str, str, dict, str]:
    """keep.google.com 로그인 후 인증 정보를 추출한다.

    Returns:
        (email, sapisid, cookies_dict, api_key)
    Raises:
        RuntimeError: 로그인 실패 또는 취소
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise RuntimeError(
            "playwright 패키지가 설치되지 않았습니다.\n\n"
            "터미널에서 다음을 실행하세요:\n"
            "  pip install playwright\n"
            "  python -m playwright install chromium"
        )

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)

    page_loaded = False
    captured_key: Optional[str] = None

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE_DIR),
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
            ],
            ignore_default_args=["--enable-automation"],
        )

        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        def _on_response(response):
            nonlocal page_loaded, captured_key
            if _KEEP_API_HOST in response.url:
                page_loaded = True
                if not captured_key:
                    m = re.search(r"[?&]key=([^&]+)", response.url)
                    if m:
                        captured_key = m.group(1)

        page.on("response", _on_response)

        try:
            page.goto("https://keep.google.com/", wait_until="load")
            _safe_wait(page, 3000)
        except Exception:
            pass

        if not page_loaded:
            start = time.time()
            while not page_loaded and (time.time() - start) < 300:
                try:
                    _safe_wait(page, 1000)
                except Exception:
                    break

        cookies_dict: dict = {}
        sapisid: str = ""
        try:
            all_cookies = ctx.cookies(["https://google.com", "https://keep.google.com"])
            for c in all_cookies:
                if c["name"] in _GOOGLE_COOKIE_NAMES or c["domain"].endswith(".google.com"):
                    cookies_dict[c["name"]] = c["value"]
            sapisid = cookies_dict.get("SAPISID", "")
        except Exception as e:
            logger.warning("쿠키 추출 오류: %s", e)

        email = ""
        try:
            email = _extract_email(page)
        except Exception:
            pass

        try:
            ctx.close()
        except Exception:
            pass

    if not sapisid:
        raise RuntimeError(
            "Google 인증 쿠키를 찾지 못했습니다.\n"
            "Google Keep 페이지가 완전히 로드될 때까지 기다려주세요."
        )

    if not page_loaded:
        raise RuntimeError(
            "Keep API 응답을 받지 못했습니다.\n"
            "로그인 후 Keep 페이지가 열릴 때까지 기다려주세요."
        )

    logger.info("인증 정보 추출 완료 (email=%s, api_key=%s…)", email or "unknown", (captured_key or "")[:8])
    return email, sapisid, cookies_dict, captured_key or ""


def _safe_wait(page, ms: int) -> None:
    try:
        page.wait_for_timeout(ms)
    except Exception:
        pass


def _extract_email(page) -> str:
    try:
        label = page.get_attribute('[aria-label*="@"]', "aria-label", timeout=2000)
        if label:
            m = re.search(r"[\w.+\-]+@[\w.\-]+\.\w+", label)
            if m:
                return m.group()
    except Exception:
        pass
    try:
        alt = page.get_attribute('img[alt*="@"]', "alt", timeout=1000)
        if alt:
            m = re.search(r"[\w.+\-]+@[\w.\-]+\.\w+", alt)
            if m:
                return m.group()
    except Exception:
        pass
    return ""
