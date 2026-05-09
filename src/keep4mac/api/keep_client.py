import logging
import uuid
from typing import Optional

import gkeepapi
import gpsoauth
import keyring

from keep4mac.core.models import ChecklistItem, NoteColor, NoteModel, NoteType

logger = logging.getLogger(__name__)

_SERVICE = "keep4mac"
_KEY_TOKEN = "master_token"
_KEY_EMAIL = "email"
_KEY_AUTH = "auth_method"   # 'password' | 'oauth'


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


class AuthError(Exception):
    pass


class SyncError(Exception):
    pass


class KeepClient:
    def __init__(self):
        self._keep = gkeepapi.Keep()
        self._email: Optional[str] = None
        self._logged_in = False

    # ── 인증 ──────────────────────────────────────────────────

    def login(self, email: str, password: str) -> None:
        """앱 비밀번호로 최초 로그인. gpsoauth로 마스터 토큰을 받아 Keychain에 저장."""
        device_id = f"{uuid.getnode():x}"

        try:
            res = gpsoauth.perform_master_login(email, password, device_id)
        except Exception as e:
            raise AuthError(f"네트워크 오류: {e}") from e

        if res.get("Error") == "NeedsBrowser":
            raise AuthError(
                "브라우저 인증이 필요합니다.\n"
                "Google 계정 보안 설정에서 앱 비밀번호를 사용하거나\n"
                "2단계 인증을 활성화해주세요."
            )

        if "Token" not in res:
            raise AuthError(f"로그인 실패: {res.get('Error', '알 수 없는 오류')}")

        master_token = res["Token"]

        try:
            self._keep.authenticate(email, master_token, sync=False)
        except Exception as e:
            raise AuthError(f"Keep 인증 실패: {e}") from e

        self._email = email
        self._logged_in = True
        keyring.set_password(_SERVICE, _KEY_TOKEN, master_token)
        keyring.set_password(_SERVICE, _KEY_EMAIL, email)
        logger.info("로그인 성공, 마스터 토큰 저장 완료")

    def resume(self) -> bool:
        """Keychain에 저장된 마스터 토큰으로 재인증."""
        email = keyring.get_password(_SERVICE, _KEY_EMAIL)
        token = keyring.get_password(_SERVICE, _KEY_TOKEN)
        if not email or not token:
            return False
        try:
            self._keep.authenticate(email, token, sync=False)
        except Exception as e:
            logger.warning("마스터 토큰 복원 실패: %s", e)
            return False
        self._email = email
        self._logged_in = True
        logger.info("마스터 토큰으로 재인증 성공")
        return True

    def logout(self) -> None:
        """로그아웃 및 Keychain 인증 정보 삭제."""
        for key in (_KEY_TOKEN, _KEY_EMAIL, _KEY_AUTH):
            try:
                keyring.delete_password(_SERVICE, key)
            except keyring.errors.PasswordDeleteError:
                pass
        self._logged_in = False
        self._email = None

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    @property
    def email(self) -> Optional[str]:
        return self._email

    # ── 동기화 ─────────────────────────────────────────────────

    def sync(self) -> None:
        """Keep 서버와 동기화."""
        if not self._logged_in:
            raise AuthError("로그인 필요")
        try:
            self._keep.sync()
        except Exception as e:
            raise SyncError(f"동기화 실패: {e}") from e

    # ── 노트 조회 ───────────────────────────────────────────────

    def get_notes(self) -> list[NoteModel]:
        """활성 노트 목록 반환. 핀 고정 노트가 앞에 옴."""
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
