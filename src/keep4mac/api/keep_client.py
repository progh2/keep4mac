import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional
from uuid import getnode as get_mac

import gkeepapi
import keyring
import requests as req_lib

from keep4mac.core.models import ChecklistItem, NoteColor, NoteModel, NoteType

logger = logging.getLogger(__name__)

_SERVICE = "keep4mac"
_KEY_SAPISID = "sapisid"
_KEY_EMAIL = "email"
_COOKIES_PATH = Path.home() / ".config" / "keep4mac" / "session.json"


# ── SAPISIDHASH 인증 ────────────────────────────────────────────


def _sapisidhash(sapisid: str) -> str:
    """SAPISID 쿠키로 SAPISIDHASH Authorization 헤더 값을 생성한다."""
    ts = int(time.time())
    data = f"{ts} {sapisid} https://keep.google.com"
    h = hashlib.sha1(data.encode()).hexdigest()
    return f"SAPISIDHASH {ts}_{h}"


class _SAPIAuth(req_lib.auth.AuthBase):
    """requests.Session에 주입하는 SAPISIDHASH 인증 객체."""

    def __init__(self, sapisid: str):
        self._sapisid = sapisid

    def __call__(self, r):
        r.headers["Authorization"] = _sapisidhash(self._sapisid)
        r.headers["X-Goog-AuthUser"] = "0"
        return r


# ── 쿠키 저장/로드 ────────────────────────────────────────────


def _save_cookies(cookies: dict) -> None:
    _COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    _COOKIES_PATH.write_text(json.dumps(cookies))


def _load_cookies() -> dict:
    if not _COOKIES_PATH.exists():
        return {}
    try:
        return json.loads(_COOKIES_PATH.read_text())
    except Exception:
        return {}


# ── 노트 변환 ──────────────────────────────────────────────────


def _parse_color(color) -> NoteColor:
    try:
        return NoteColor(color.value)
    except (AttributeError, ValueError):
        return NoteColor.DEFAULT


def _to_model(note) -> NoteModel:
    color = _parse_color(note.color)

    if isinstance(note, gkeepapi.node.List):
        items = [
            ChecklistItem(text=item.text, checked=item.checked)
            for item in note.items
            if not item.deleted
        ]
        return NoteModel(
            id=note.id,
            title=note.title or "",
            text="",
            note_type=NoteType.LIST,
            pinned=note.pinned,
            color=color,
            checklist_items=items,
        )

    return NoteModel(
        id=note.id,
        title=note.title or "",
        text=note.text or "",
        note_type=NoteType.TEXT,
        pinned=note.pinned,
        color=color,
    )


# ── 예외 ───────────────────────────────────────────────────────


class AuthError(Exception):
    pass


class SyncError(Exception):
    pass


# ── KeepClient ─────────────────────────────────────────────────


class KeepClient:
    def __init__(self):
        self._keep = gkeepapi.Keep()
        self._email: Optional[str] = None
        self._logged_in = False

    # ── 인증 ──────────────────────────────────────────────────

    def login_with_browser(self, email: str, sapisid: str, cookies: dict) -> None:
        """브라우저에서 추출한 SAPISID/쿠키로 gkeepapi 세션을 인증한다."""
        self._inject_auth(sapisid, cookies)

        try:
            # load()로 gkeepapi 내부 상태 초기화 후 sync()로 노트 가져오기
            dummy_auth = gkeepapi.APIAuth(gkeepapi.Keep.OAUTH_SCOPES)
            dummy_auth._email = email or "user@gmail.com"
            dummy_auth._device_id = f"{get_mac():x}"
            dummy_auth._auth_token = "dummy"
            self._keep.load(dummy_auth, sync=False)
            self._keep.sync()
        except Exception as e:
            raise AuthError(f"Keep 동기화 실패: {e}") from e

        self._email = email
        self._logged_in = True
        keyring.set_password(_SERVICE, _KEY_SAPISID, sapisid)
        keyring.set_password(_SERVICE, _KEY_EMAIL, email or "")
        _save_cookies(cookies)
        logger.info("브라우저 로그인 성공 (email=%s)", email)

    def resume(self) -> bool:
        """저장된 SAPISID/쿠키로 재인증을 시도한다."""
        email = keyring.get_password(_SERVICE, _KEY_EMAIL)
        sapisid = keyring.get_password(_SERVICE, _KEY_SAPISID)
        cookies = _load_cookies()

        if not sapisid or not cookies:
            return False

        self._inject_auth(sapisid, cookies)

        try:
            dummy_auth = gkeepapi.APIAuth(gkeepapi.Keep.OAUTH_SCOPES)
            dummy_auth._email = email or "user@gmail.com"
            dummy_auth._device_id = f"{get_mac():x}"
            dummy_auth._auth_token = "dummy"
            self._keep.load(dummy_auth, sync=False)
        except Exception as e:
            logger.warning("재인증 실패: %s", e)
            return False

        self._email = email
        self._logged_in = True
        logger.info("저장된 세션으로 재인증 성공")
        return True

    def logout(self) -> None:
        """로그아웃 및 저장된 인증 정보 삭제."""
        for key in (_KEY_SAPISID, _KEY_EMAIL):
            try:
                keyring.delete_password(_SERVICE, key)
            except keyring.errors.PasswordDeleteError:
                pass
        if _COOKIES_PATH.exists():
            _COOKIES_PATH.unlink()
        self._logged_in = False
        self._email = None

    def _inject_auth(self, sapisid: str, cookies: dict) -> None:
        """gkeepapi의 requests.Session에 SAPISIDHASH 인증과 쿠키를 주입한다."""
        sapi_auth = _SAPIAuth(sapisid)
        for api_obj in [self._keep._keep_api, self._keep._reminders_api]:
            api_obj._session.auth = sapi_auth
            api_obj._session.cookies.update(cookies)

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    @property
    def email(self) -> Optional[str]:
        return self._email

    # ── 동기화 ─────────────────────────────────────────────────

    def sync(self) -> None:
        if not self._logged_in:
            raise AuthError("로그인 필요")
        try:
            self._keep.sync()
        except Exception as e:
            raise SyncError(f"동기화 실패: {e}") from e

    # ── 노트 조회 ───────────────────────────────────────────────

    def get_notes(self) -> list[NoteModel]:
        notes = [
            _to_model(n)
            for n in self._keep.all()
            if not n.trashed and not n.archived
        ]
        notes.sort(key=lambda n: (not n.pinned, n.title.lower()))
        return notes

    def get_note(self, note_id: str) -> Optional[NoteModel]:
        note = self._keep.get(note_id)
        return _to_model(note) if note else None

    # ── 노트 수정 ───────────────────────────────────────────────

    def create_note(self, title: str, text: str) -> NoteModel:
        note = self._keep.createNote(title, text)
        self._keep.sync()
        return _to_model(note)

    def update_note(self, note_id: str, title: str, text: str) -> None:
        note = self._keep.get(note_id)
        if not note:
            return
        note.title = title
        if isinstance(note, gkeepapi.node.Note):
            note.text = text
        self._keep.sync()

    def delete_note(self, note_id: str) -> None:
        note = self._keep.get(note_id)
        if note:
            note.trash()
            self._keep.sync()
