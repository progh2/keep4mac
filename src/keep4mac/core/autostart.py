"""로그인 시 자동 시작 관리 — macOS LaunchAgent / Windows Registry."""
import sys

if sys.platform == "darwin":
    import os
    from pathlib import Path

    _LABEL = "com.keep4mac.app"
    _PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{_LABEL}.plist"

    def _app_executable() -> str | None:
        if getattr(sys, "frozen", False):
            return sys.executable
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
        if is_enabled():
            disable()
            return False
        else:
            return enable()

elif sys.platform == "win32":
    import winreg

    _APP_NAME = "keep4mac"
    _RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

    def is_enabled() -> bool:
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY)
            winreg.QueryValueEx(k, _APP_NAME)
            winreg.CloseKey(k)
            return True
        except OSError:
            return False

    def enable() -> bool:
        if not getattr(sys, "frozen", False):
            return False
        try:
            k = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(k, _APP_NAME, 0, winreg.REG_SZ, sys.executable)
            winreg.CloseKey(k)
            return True
        except OSError:
            return False

    def disable() -> bool:
        try:
            k = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(k, _APP_NAME)
            winreg.CloseKey(k)
        except OSError:
            pass
        return True

    def toggle() -> bool:
        if is_enabled():
            disable()
            return False
        else:
            return enable()

else:
    # 지원되지 않는 플랫폼 — 스텁
    def is_enabled() -> bool:
        return False

    def enable() -> bool:
        return False

    def disable() -> bool:
        return True

    def toggle() -> bool:
        return False
