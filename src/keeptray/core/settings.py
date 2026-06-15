import json
import os
import sys
from pathlib import Path


def _get_settings_path() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "keeptray" / "settings.json"
    return Path.home() / ".config" / "keeptray" / "settings.json"


_SETTINGS_PATH = _get_settings_path()
_OLD_PATH = Path.home() / ".config" / "keeptray" / "settings.json"


def _migrate_if_needed() -> None:
    """Windows에서 구 경로(~/.config)→ 새 경로(%APPDATA%) 자동 마이그레이션."""
    if sys.platform == "win32" and _OLD_PATH != _SETTINGS_PATH:
        if _OLD_PATH.exists() and not _SETTINGS_PATH.exists():
            _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            _OLD_PATH.rename(_SETTINGS_PATH)


_migrate_if_needed()


def _load() -> dict:
    if not _SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    fd = os.open(str(_SETTINGS_PATH), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, content)
    finally:
        os.close(fd)


def get_my_email() -> str:
    return _load().get("my_email", "")


def set_my_email(email: str) -> None:
    data = _load()
    data["my_email"] = email
    _save(data)


def get_window_pos() -> list[int] | None:
    pos = _load().get("window_pos")
    if isinstance(pos, list) and len(pos) == 2:
        return pos
    return None


def set_window_pos(x: int, y: int) -> None:
    data = _load()
    data["window_pos"] = [x, y]
    _save(data)


def get_sort() -> dict:
    """정렬 설정 반환. key: 'updated'|'created'|'title', desc: bool"""
    s = _load().get("sort", {})
    return {
        "key": s.get("key", "updated"),
        "desc": s.get("desc", True),
    }


def set_sort(key: str, desc: bool) -> None:
    data = _load()
    data["sort"] = {"key": key, "desc": desc}
    _save(data)


_FONT_DEFAULTS: dict[str, dict] = {
    "list_title":   {"family": "", "size": 13},
    "list_content": {"family": "", "size": 12},
    "editor_title": {"family": "", "size": 16},
    "editor_body":  {"family": "", "size": 13},
}


def get_fonts() -> dict:
    saved = _load().get("fonts", {})
    result = {}
    for key, default in _FONT_DEFAULTS.items():
        entry = saved.get(key, {})
        result[key] = {
            "family": entry.get("family", default["family"]),
            "size": int(entry.get("size", default["size"])),
        }
    return result


def set_fonts(fonts: dict) -> None:
    data = _load()
    data["fonts"] = fonts
    _save(data)


def get_font_defaults() -> dict:
    return {k: dict(v) for k, v in _FONT_DEFAULTS.items()}


def get_theme() -> str:
    """테마 반환: 'system' | 'light' | 'dark'"""
    return _load().get("theme", "system")


def set_theme(theme: str) -> None:
    data = _load()
    data["theme"] = theme
    _save(data)
