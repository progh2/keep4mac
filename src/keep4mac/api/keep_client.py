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
_SESSION_PATH = Path.home() / ".config" / "keep4mac" / "session.json"

# keep.google.com이 실제로 사용하는 API 엔드포인트 (SAPISIDHASH 인증 사용)
_BROWSER_API_URL = "https://notes-pa.clients6.google.com/notes/v1/"


# ── SAPISIDHASH 인증 ────────────────────────────────────────────


def _sapisidhash(sapisid: str) -> str:
    ts = int(time.time())
    data = f"{ts} {sapisid} https://keep.google.com"
    h = hashlib.sha1(data.encode()).hexdigest()
    return f"SAPISIDHASH {ts}_{h}"


class _SAPIAuth(req_lib.auth.AuthBase):
    def __init__(self, sapisid: str):
        self._sapisid = sapisid

    def __call__(self, r):
        r.headers["Authorization"] = _sapisidhash(self._sapisid)
        r.headers["X-Goog-AuthUser"] = "0"
        r.headers["Origin"] = "https://keep.google.com"
        r.headers["Referer"] = "https://keep.google.com/"
        return r


# ── 세션 저장/로드 ─────────────────────────────────────────────


def _save_session(cookies: dict, api_key: str) -> None:
    _SESSION_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SESSION_PATH.write_text(json.dumps({"cookies": cookies, "api_key": api_key}))


def _load_session() -> tuple[dict, str]:
    if not _SESSION_PATH.exists():
        return {}, ""
    try:
        data = json.loads(_SESSION_PATH.read_text())
        return data.get("cookies", {}), data.get("api_key", "")
    except Exception:
        return {}, ""


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

    def login_with_browser(self, email: str, sapisid: str, cookies: dict, api_key: str) -> None:
        """브라우저 세션 정보로 gkeepapi를 인증하고 Keep과 동기화한다."""
        self._inject_auth(sapisid, cookies, api_key)

        try:
            dummy_auth = self._make_dummy_auth(email)
            self._keep.load(dummy_auth, sync=False)
            self._keep.sync()
        except Exception as e:
            raise AuthError(f"Keep 동기화 실패: {e}") from e

        self._email = email
        self._logged_in = True
        keyring.set_password(_SERVICE, _KEY_SAPISID, sapisid)
        keyring.set_password(_SERVICE, _KEY_EMAIL, email or "")
        _save_session(cookies, api_key)
        logger.info("로그인 성공 (email=%s)", email)

    def resume(self) -> bool:
        """저장된 세션 정보로 재인증한다."""
        email = keyring.get_password(_SERVICE, _KEY_EMAIL)
        sapisid = keyring.get_password(_SERVICE, _KEY_SAPISID)
        cookies, api_key = _load_session()

        if not sapisid or not cookies:
            return False

        self._inject_auth(sapisid, cookies, api_key)

        try:
            dummy_auth = self._make_dummy_auth(email)
            self._keep.load(dummy_auth, sync=False)
        except Exception as e:
            logger.warning("재인증 실패: %s", e)
            return False

        self._email = email
        self._logged_in = True
        logger.info("저장된 세션으로 재인증 성공")
        return True

    def logout(self) -> None:
        for key in (_KEY_SAPISID, _KEY_EMAIL):
            try:
                keyring.delete_password(_SERVICE, key)
            except keyring.errors.PasswordDeleteError:
                pass
        if _SESSION_PATH.exists():
            _SESSION_PATH.unlink()
        self._logged_in = False
        self._email = None

    def _inject_auth(self, sapisid: str, cookies: dict, api_key: str) -> None:
        """gkeepapi의 requests 세션을 브라우저 인증(SAPISIDHASH)으로 패치한다."""
        sapi_auth = _SAPIAuth(sapisid)
        params = {"alt": "json"}
        if api_key:
            params["key"] = api_key

        for api_obj in [self._keep._keep_api, self._keep._reminders_api]:
            # ① 엔드포인트를 브라우저용으로 변경
            api_obj._base_url = _BROWSER_API_URL
            # ② SAPISIDHASH 인증 + 쿠키 주입
            api_obj._session.auth = sapi_auth
            api_obj._session.cookies.update(cookies)
            # ③ 필수 쿼리 파라미터 고정
            api_obj._session.params = params

    def _make_dummy_auth(self, email: str) -> gkeepapi.APIAuth:
        """gkeepapi 내부 인증 체크를 통과하는 더미 APIAuth를 생성한다.
        실제 HTTP 인증은 session.auth(_SAPIAuth)가 담당한다.
        """
        auth = gkeepapi.APIAuth(gkeepapi.Keep.OAUTH_SCOPES)
        auth._email = email or "user@gmail.com"
        auth._device_id = f"{get_mac():x}"
        auth._auth_token = "dummy"
        # OAuth 재발급 시도(refresh)를 차단 — SAPISIDHASH 방식이므로 불필요
        auth.refresh = lambda: None
        return auth

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
