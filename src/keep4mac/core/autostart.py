"""macOS LaunchAgent 기반 로그인 시 자동 시작 관리."""
import os
import sys
from pathlib import Path

_LABEL = "com.keep4mac.app"
_PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{_LABEL}.plist"


def _app_executable() -> str | None:
    if getattr(sys, "frozen", False):
        return sys.executable  # .app/Contents/MacOS/keep4mac
    return None


def is_enabled() -> bool:
    return _PLIST_PATH.exists()


def enable() -> bool:
    exe = _app_executable()
    if not exe:
        return False
    _PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PLIST_PATH.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{exe}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
""")
    return True


def disable() -> bool:
    if _PLIST_PATH.exists():
        _PLIST_PATH.unlink()
    return True


def toggle() -> bool:
    """토글 후 새 상태(enabled 여부)를 반환."""
    if is_enabled():
        disable()
        return False
    else:
        return enable()
