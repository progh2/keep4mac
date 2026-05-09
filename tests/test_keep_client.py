from unittest.mock import MagicMock, patch

import gkeepapi
import pytest

from keep4mac.api.keep_client import AuthError, KeepClient, SyncError
from keep4mac.core.models import NoteColor, NoteType


def _make_note(title="제목", text="내용", pinned=False, color_value="DEFAULT", trashed=False, archived=False):
    note = MagicMock(spec=gkeepapi.node.Note)
    note.id = "note-001"
    note.title = title
    note.text = text
    note.pinned = pinned
    note.color = MagicMock()
    note.color.value = color_value
    note.trashed = trashed
    note.archived = archived
    return note


@pytest.fixture
def client():
    return KeepClient()


class TestLogin:
    def test_login_success_saves_token(self, client):
        with (
            patch.object(client._keep, "login"),
            patch.object(client._keep, "getMasterToken", return_value="tok123"),
            patch("keep4mac.api.keep_client.keyring.set_password") as mock_set,
        ):
            client.login("user@gmail.com", "app-password")

        assert client.is_logged_in
        assert client.email == "user@gmail.com"
        mock_set.assert_any_call("keep4mac", "master_token", "tok123")

    def test_login_failure_raises_auth_error(self, client):
        with patch.object(client._keep, "login", side_effect=Exception("bad creds")):
            with pytest.raises(AuthError):
                client.login("user@gmail.com", "wrong")

        assert not client.is_logged_in


class TestResume:
    def test_resume_success(self, client):
        with (
            patch("keep4mac.api.keep_client.keyring.get_password", side_effect=["user@gmail.com", "tok123"]),
            patch.object(client._keep, "resume"),
        ):
            result = client.resume()

        assert result is True
        assert client.is_logged_in

    def test_resume_no_token_returns_false(self, client):
        with patch("keep4mac.api.keep_client.keyring.get_password", return_value=None):
            result = client.resume()

        assert result is False
        assert not client.is_logged_in


class TestGetNotes:
    def test_returns_active_notes_only(self, client):
        active = _make_note(title="활성")
        trashed = _make_note(title="삭제됨", trashed=True)
        archived = _make_note(title="보관됨", archived=True)

        client._logged_in = True
        with patch.object(client._keep, "all", return_value=[active, trashed, archived]):
            notes = client.get_notes()

        assert len(notes) == 1
        assert notes[0].title == "활성"

    def test_pinned_notes_come_first(self, client):
        n1 = _make_note(title="일반", pinned=False)
        n2 = _make_note(title="핀고정", pinned=True)
        n1.id, n2.id = "a", "b"

        client._logged_in = True
        with patch.object(client._keep, "all", return_value=[n1, n2]):
            notes = client.get_notes()

        assert notes[0].pinned is True

    def test_color_parsed_correctly(self, client):
        note = _make_note(color_value="RED")
        client._logged_in = True
        with patch.object(client._keep, "all", return_value=[note]):
            notes = client.get_notes()

        assert notes[0].color == NoteColor.RED

    def test_note_type_is_text(self, client):
        note = _make_note()
        client._logged_in = True
        with patch.object(client._keep, "all", return_value=[note]):
            notes = client.get_notes()

        assert notes[0].note_type == NoteType.TEXT


class TestSync:
    def test_sync_raises_when_not_logged_in(self, client):
        with pytest.raises(AuthError):
            client.sync()

    def test_sync_raises_sync_error_on_failure(self, client):
        client._logged_in = True
        with patch.object(client._keep, "sync", side_effect=Exception("network")):
            with pytest.raises(SyncError):
                client.sync()
