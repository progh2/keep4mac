import json
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.expanduser("~/.config/keep4mac")
CREDENTIALS_FILE = os.path.join(CONFIG_DIR, "credentials.json")
TOKEN_FILE = os.path.join(CONFIG_DIR, "token.json")

# Keep 내부 API 스코프 + 이메일 확인 스코프
SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/memento",
]


class OAuthError(Exception):
    pass


class OAuthFlow:
    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    @property
    def has_credentials(self) -> bool:
        return os.path.exists(CREDENTIALS_FILE)

    def set_credentials_file(self, src_path: str) -> None:
        """사용자가 선택한 credentials.json 파일을 설정 디렉토리에 복사."""
        import shutil
        shutil.copy2(src_path, CREDENTIALS_FILE)
        logger.info("credentials.json 저장 완료: %s", CREDENTIALS_FILE)

    def authenticate(self) -> tuple[str, str]:
        """
        브라우저 OAuth 플로우 실행. (email, access_token) 반환.
        저장된 토큰이 유효하면 브라우저 없이 반환.
        """
        if not self.has_credentials:
            raise FileNotFoundError(
                f"credentials.json 없음: {CREDENTIALS_FILE}"
            )

        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        creds: Optional[Credentials] = self._load_token()

        if creds and creds.valid:
            return self._get_email(creds.token), creds.token

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_token(creds)
                return self._get_email(creds.token), creds.token
            except Exception as e:
                logger.warning("토큰 갱신 실패, 재인증 진행: %s", e)

        # 브라우저 OAuth 플로우
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0, open_browser=True)
        except Exception as e:
            raise OAuthError(f"Google 로그인 실패: {e}") from e

        self._save_token(creds)
        email = self._get_email(creds.token)
        logger.info("OAuth 인증 성공: %s", email)
        return email, creds.token

    def clear(self) -> None:
        """저장된 OAuth 토큰 삭제 (로그아웃)."""
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)

    # ── 내부 ─────────────────────────────────────────────────

    def _load_token(self):
        if not os.path.exists(TOKEN_FILE):
            return None
        try:
            from google.oauth2.credentials import Credentials
            return Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.warning("저장된 토큰 로드 실패: %s", e)
            return None

    def _save_token(self, creds) -> None:
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    def _get_email(self, access_token: str) -> str:
        import requests as req
        resp = req.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("email", "")
