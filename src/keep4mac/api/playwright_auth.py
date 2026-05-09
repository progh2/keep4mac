import logging
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROFILE_DIR = Path.home() / ".config" / "keep4mac" / "chrome_profile"


def run_browser_login() -> tuple[str, str]:
    """keep.google.com 브라우저 로그인 후 Bearer 토큰을 캡처한다.

    Returns:
        (email, auth_token) — email은 빈 문자열일 수 있음
    Raises:
        RuntimeError: 로그인 실패 또는 타임아웃
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

    captured_token: Optional[str] = None

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

        def _on_request(request):
            nonlocal captured_token
            if captured_token:
                return
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer ") and (
                "notes-pa.clients6.google.com" in request.url
                or "/notes/v1" in request.url
            ):
                captured_token = auth[7:]
                logger.debug("Keep Bearer 토큰 캡처 완료")

        page.on("request", _on_request)
        page.goto("https://keep.google.com/", wait_until="load")
        page.wait_for_timeout(2000)

        # 이미 로그인된 경우 즉시 토큰 캡처됨
        # 아직 없으면 사용자 로그인 완료까지 최대 5분 대기
        if not captured_token:
            start = time.time()
            while not captured_token and (time.time() - start) < 300:
                page.wait_for_timeout(1000)

        # 이메일 추출 시도
        email = _extract_email(page)

        ctx.close()

    if not captured_token:
        raise RuntimeError(
            "인증 토큰을 캡처하지 못했습니다.\n"
            "5분 이내에 Google 로그인을 완료해주세요."
        )

    return email, captured_token


def _extract_email(page) -> str:
    """Keep 페이지에서 Google 계정 이메일을 추출한다."""
    try:
        # Google 계정 버튼 aria-label에서 이메일 파싱
        label = page.get_attribute('[aria-label*="@"]', "aria-label", timeout=2000)
        if label:
            m = re.search(r"[\w.+\-]+@[\w.\-]+\.\w+", label)
            if m:
                return m.group()
    except Exception:
        pass

    try:
        # 헤더 영역의 계정 이미지 alt 속성
        alt = page.get_attribute('img[alt*="@"]', "alt", timeout=1000)
        if alt:
            m = re.search(r"[\w.+\-]+@[\w.\-]+\.\w+", alt)
            if m:
                return m.group()
    except Exception:
        pass

    return ""
