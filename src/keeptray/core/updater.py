"""GitHub Releases 기반 자동 업데이트 로직."""
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Callable, Optional

import requests

GITHUB_REPO = "progh2/keeptray"
_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_HEADERS = {"Accept": "application/vnd.github.v3+json", "User-Agent": "keeptray-updater"}
_MAX_EXTRACT_SIZE = 500 * 1024 * 1024  # ZIP 압축 해제 최대 500 MB


# ── 버전 비교 ──────────────────────────────────────────────────

def _parse(v: str) -> tuple:
    return tuple(int(x) for x in v.lstrip("v").split("."))


def current_version() -> str:
    from keeptray import __version__
    return __version__


# ── 업데이트 확인 ──────────────────────────────────────────────

def check_update() -> Optional[dict]:
    """최신 릴리즈가 현재 버전보다 높으면 릴리즈 정보를 반환, 아니면 None."""
    try:
        resp = requests.get(_API_URL, headers=_HEADERS, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        tag = data.get("tag_name", "")
        if not tag:
            return None
        if _parse(tag) <= _parse(current_version()):
            return None
        return {
            "version": tag,
            "notes": (data.get("body") or "").strip(),
            "assets": data.get("assets", []),
        }
    except Exception:
        return None


# ── 에셋 URL ───────────────────────────────────────────────────

def get_asset(assets: list) -> Optional[dict]:
    """플랫폼에 맞는 첨부 파일을 반환한다."""
    if sys.platform == "darwin":
        suffix = ".dmg"
    elif sys.platform == "win32":
        suffix = "-win.zip"
    else:
        return None
    for a in assets:
        if a.get("name", "").endswith(suffix):
            return a
    return None


# ── 다운로드 ──────────────────────────────────────────────────

def download(url: str, progress_cb: Optional[Callable[[int, int], None]] = None) -> Path:
    """URL을 임시 파일로 다운로드한다. progress_cb(downloaded, total) 호출."""
    if not url.startswith("https://"):
        raise ValueError(f"HTTPS URL만 허용됩니다: {url}")
    suffix = ".dmg" if url.endswith(".dmg") else ".zip"
    tmp = Path(tempfile.mktemp(suffix=suffix, prefix="keeptray_upd_"))
    with requests.get(url, stream=True, timeout=120, headers=_HEADERS) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length", 0))
        done = 0
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(65536):
                if chunk:
                    f.write(chunk)
                    done += len(chunk)
                    if progress_cb and total:
                        progress_cb(done, total)
    return tmp


# ── 설치: macOS ───────────────────────────────────────────────

def apply_macos(dmg_path: Path) -> None:
    """DMG 마운트 → .app 교체 → 언마운트 → 재실행."""
    mount_out = subprocess.check_output(
        ["/usr/bin/hdiutil", "attach", str(dmg_path), "-nobrowse", "-quiet", "-plist"],
        stderr=subprocess.DEVNULL,
    ).decode()

    # plist에서 마운트 포인트 파싱 (XML 의존성 없이 문자열로)
    mount_point: Optional[str] = None
    for line in mount_out.splitlines():
        line = line.strip()
        if line.startswith("<string>/Volumes/"):
            mount_point = line[8:-9]  # <string> … </string>
            break

    if not mount_point:
        raise RuntimeError("DMG 마운트 포인트를 찾을 수 없습니다.")

    try:
        apps = list(Path(mount_point).glob("*.app"))
        if not apps:
            raise RuntimeError("DMG에서 .app을 찾을 수 없습니다.")
        src_app = apps[0]

        # 현재 실행 중인 .app 경로 (.app/Contents/MacOS/keeptray → 3단계 상위)
        if getattr(sys, "frozen", False):
            current_app = Path(sys.executable).parent.parent.parent
        else:
            raise RuntimeError("개발 모드에서는 자동 업데이트를 지원하지 않습니다.")

        dest_parent = current_app.parent
        subprocess.run(
            ["/usr/bin/rsync", "-a", "--delete",
             str(src_app) + "/", str(current_app) + "/"],
            check=True,
        )
        # 재실행
        subprocess.Popen(["/usr/bin/open", str(current_app)])
    finally:
        subprocess.run(
            ["/usr/bin/hdiutil", "detach", mount_point, "-quiet", "-force"],
            capture_output=True,
        )
        dmg_path.unlink(missing_ok=True)


# ── 설치: Windows ─────────────────────────────────────────────

def apply_windows(zip_path: Path) -> None:
    """ZIP 압축 해제 → 배치 스크립트로 xcopy 후 재실행."""
    update_dir = Path(tempfile.mkdtemp(prefix="keeptray_upd_"))
    with zipfile.ZipFile(zip_path, "r") as z:
        total_size = sum(i.file_size for i in z.infolist())
        if total_size > _MAX_EXTRACT_SIZE:
            raise RuntimeError(f"압축 해제 크기 초과: {total_size // 1024 // 1024}MB")
        z.extractall(update_dir)
    zip_path.unlink(missing_ok=True)

    if not getattr(sys, "frozen", False):
        raise RuntimeError("개발 모드에서는 자동 업데이트를 지원하지 않습니다.")

    exe = Path(sys.executable)
    install_dir = exe.parent

    # 압축 해제된 keeptray/ 폴더
    extracted = update_dir / "keeptray"
    if not extracted.exists():
        extracted = update_dir

    import os
    fd, bat_path = tempfile.mkstemp(suffix=".bat", prefix="keeptray_upd_")
    try:
        os.write(fd, (
            "@echo off\r\n"
            "timeout /t 3 /nobreak > nul\r\n"
            f'xcopy /e /y /q "{extracted}\\" "{install_dir}\\"\r\n'
            f'start "" "{install_dir / exe.name}"\r\n'
            f'rd /s /q "{update_dir}"\r\n'
            'del "%~f0"\r\n'
        ).encode("utf-8"))
    finally:
        os.close(fd)
    bat = Path(bat_path)
    subprocess.Popen(
        ["cmd.exe", "/c", str(bat)],
        creationflags=subprocess.CREATE_NO_WINDOW,
        close_fds=True,
    )


def apply_update(path: Path) -> None:
    """플랫폼에 맞는 설치 함수를 호출한다."""
    if sys.platform == "darwin":
        apply_macos(path)
    elif sys.platform == "win32":
        apply_windows(path)
    else:
        raise RuntimeError(f"지원하지 않는 플랫폼: {sys.platform}")
