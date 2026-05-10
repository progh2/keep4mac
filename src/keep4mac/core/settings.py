import json
from pathlib import Path

_SETTINGS_PATH = Path.home() / ".config" / "keep4mac" / "settings.json"


def _load() -> dict:
    if not _SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save(data: dict) -> None:
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


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
