import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import getnode as get_mac

import gkeepapi
import keyring
import requests as req_lib

from keeptray.core.models import ChecklistItem, NoteColor, NoteModel, NoteType

logger = logging.getLogger(__name__)

_SERVICE = "keeptray"
_KEY_SAPISID = "sapisid"
_KEY_EMAIL = "email"
_SESSION_PATH = Path.home() / ".config" / "keeptray" / "session.json"
_IMAGE_CACHE_DIR = Path.home() / ".config" / "keeptray" / "image_cache"
_NOTES_CACHE_PATH = Path.home() / ".config" / "keeptray" / "notes_cache.json"
_SYNC_INTERVAL = 300  # 초: 5분 이내 재동기화 생략

# keep.google.com이 실제로 사용하는 API 엔드포인트 (SAPISIDHASH 인증 사용)
_BROWSER_API_URL = "https://notes-pa.clients6.google.com/notes/v1/"


def _cache_path(url: str) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()
    return _IMAGE_CACHE_DIR / key


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


def _find_image_url(note) -> str | None:
    try:
        for blob in getattr(note, "blobs", []):
            inner = getattr(blob, "blob", None)
            if inner is None:
                continue
            if inner.type == gkeepapi.node.BlobType.Image:
                blob_sid = getattr(blob, "server_id", None)
                note_sid = getattr(note, "server_id", None)
                if blob_sid and note_sid:
                    return f"https://keep.google.com/media/v2/{note_sid}/{blob_sid}"
    except Exception:
        pass
    return None


def _to_model(note) -> NoteModel:
    color = _parse_color(note.color)
    image_url = _find_image_url(note)

    ts = getattr(note, "timestamps", None)
    updated = (ts.updated if ts and ts.updated else None)

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
            image_url=image_url,
            updated=updated,
        )

    return NoteModel(
        id=note.id,
        title=note.title or "",
        text=note.text or "",
        note_type=NoteType.TEXT,
        pinned=note.pinned,
        color=color,
        image_url=image_url,
        updated=updated,
    )


# ── 노트 캐시 직렬화 ──────────────────────────────────────────


def _note_to_dict(n: "NoteModel") -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "text": n.text,
        "note_type": n.note_type.value,
        "pinned": n.pinned,
        "color": n.color.value,
        "checklist_items": [{"text": i.text, "checked": i.checked} for i in n.checklist_items],
        "image_url": n.image_url,
        "updated": n.updated.isoformat() if n.updated else None,
    }


def _note_from_dict(d: dict) -> "NoteModel":
    updated_str = d.get("updated")
    updated = datetime.fromisoformat(updated_str) if updated_str else None
    return NoteModel(
        id=d["id"],
        title=d.get("title", ""),
        text=d.get("text", ""),
        note_type=NoteType(d.get("note_type", "text")),
        pinned=d.get("pinned", False),
        color=NoteColor(d.get("color", "DEFAULT")),
        checklist_items=[ChecklistItem(**i) for i in d.get("checklist_items", [])],
        image_url=d.get("image_url"),
        updated=updated,
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
        self._sapisid: str = ""
        self._cookies: dict = {}
        self._last_sync_time: float = 0.0
        self._notes_memory: list[NoteModel] = []

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
        self._sapisid = sapisid
        self._cookies = cookies
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

    @property
    def needs_sync(self) -> bool:
        """마지막 동기화로부터 _SYNC_INTERVAL 초 이상 경과했으면 True."""
        return time.time() - self._last_sync_time > _SYNC_INTERVAL

    def sync(self) -> None:
        if not self._logged_in:
            raise AuthError("로그인 필요")
        try:
            self._keep.sync()
            self._last_sync_time = time.time()
        except Exception as e:
            raise SyncError(f"동기화 실패: {e}") from e

    # ── 노트 조회 ───────────────────────────────────────────────

    def get_notes(self) -> list[NoteModel]:
        raw = [n for n in self._keep.all() if not n.trashed and not n.archived]
        raw.sort(key=lambda n: (
            0 if n.pinned else 1,
            -(n.timestamps.updated.timestamp() if n.timestamps and n.timestamps.updated else 0),
        ))
        notes = [_to_model(n) for n in raw]
        self._notes_memory = notes
        self._save_notes_cache(notes)
        return notes

    def get_cached_notes(self) -> list[NoteModel]:
        """네트워크 없이 메모리 캐시에서 즉시 반환."""
        return self._notes_memory

    def load_disk_cache(self) -> list[NoteModel]:
        """앱 시작 시 디스크 캐시에서 노트를 복원한다."""
        if not _NOTES_CACHE_PATH.exists():
            return []
        try:
            data = json.loads(_NOTES_CACHE_PATH.read_text(encoding="utf-8"))
            notes = [_note_from_dict(d) for d in data]
            self._notes_memory = notes
            logger.info("디스크 캐시 로드: %d개 노트", len(notes))
            return notes
        except Exception as e:
            logger.warning("노트 캐시 로드 실패: %s", e)
            return []

    def _save_notes_cache(self, notes: list[NoteModel]) -> None:
        try:
            _NOTES_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
            _NOTES_CACHE_PATH.write_text(
                json.dumps([_note_to_dict(n) for n in notes], ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning("노트 캐시 저장 실패: %s", e)

    def fetch_image(self, url: str) -> bytes | None:
        cached = _cache_path(url)
        if cached.exists():
            return cached.read_bytes()

        if not self._sapisid:
            return None
        try:
            resp = req_lib.get(
                url,
                auth=_SAPIAuth(self._sapisid),
                cookies=self._cookies,
                timeout=10,
            )
            if resp.status_code == 200:
                _IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(resp.content)
                return resp.content
        except Exception as e:
            logger.warning("이미지 다운로드 실패: %s", e)
        return None

    def get_note(self, note_id: str) -> Optional[NoteModel]:
        note = self._keep.get(note_id)
        return _to_model(note) if note else None

    # ── 노트 수정 ───────────────────────────────────────────────

    def create_note(self, title: str, text: str, color: NoteColor = NoteColor.DEFAULT, pinned: bool = False) -> NoteModel:
        note = self._keep.createNote(title, text)
        note.color = gkeepapi.node.ColorValue(color.value)
        note.pinned = pinned
        model = _to_model(note)
        model.updated = datetime.now(timezone.utc)
        self._notes_memory = [model] + self._notes_memory
        return model

    def toggle_pin(self, note_id: str) -> bool:
        """핀 상태를 토글하고 새 상태를 반환한다."""
        note = self._keep.get(note_id)
        if not note:
            return False
        note.pinned = not note.pinned
        self._keep.sync()
        return note.pinned

    def update_note(self, note_id: str, title: str, text: str, color: NoteColor | None = None) -> None:
        note = self._keep.get(note_id)
        if not note:
            return
        note.title = title
        if isinstance(note, gkeepapi.node.Note):
            note.text = text
        if color is not None:
            note.color = gkeepapi.node.ColorValue(color.value)
        self._keep.sync()
        model = _to_model(note)
        self._notes_memory = [model if n.id == note_id else n for n in self._notes_memory]

    def update_checklist(self, note_id: str, title: str, items: list[tuple[str, bool]], color: NoteColor | None = None) -> None:
        note = self._keep.get(note_id)
        if not note or not isinstance(note, gkeepapi.node.List):
            return
        note.title = title
        existing = [i for i in note.items if not i.deleted]
        for idx, (text, checked) in enumerate(items):
            if idx < len(existing):
                existing[idx].text = text
                existing[idx].checked = checked
        if color is not None:
            note.color = gkeepapi.node.ColorValue(color.value)
        self._keep.sync()
        model = _to_model(note)
        self._notes_memory = [model if n.id == note_id else n for n in self._notes_memory]

    def delete_note(self, note_id: str) -> None:
        note = self._keep.get(note_id)
        if note:
            note.trash()
            self._notes_memory = [n for n in self._notes_memory if n.id != note_id]

    def delete_image(self, note_id: str, image_url: str) -> None:
        """이미지 URL에서 blob_server_id를 추출해 해당 블롭을 삭제한다."""
        blob_sid = image_url.rstrip("/").split("/")[-1]
        note = self._keep.get(note_id)
        if not note:
            return
        for blob in list(getattr(note, "blobs", [])):
            if blob.server_id == blob_sid:
                blob.delete()
                break
        self._keep.sync()
        cached = _cache_path(image_url)
        if cached.exists():
            cached.unlink()
