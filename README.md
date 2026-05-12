# keeptray

Google Keep 데스크톱 트레이 앱 (macOS · Windows). 트레이 아이콘을 클릭하면 Keep 노트를 바로 조회·작성·수정·삭제할 수 있습니다.

## 주요 기능

- **메뉴바 상주** — 앱이 Dock 없이 메뉴바/트레이 아이콘으로 실행됩니다
- **트레이 직접 클릭** — 아이콘 클릭 시 노트 목록 패널이 즉시 열립니다 (macOS 우클릭 시 종료 메뉴)
- **노트 목록 조회** — 최신 노트 목록을 카드 형태로 표시, 이미지 썸네일 지원
- **노트 정렬** — 수정일·생성일·제목 기준 오름차순/내림차순 정렬
- **노트 작성·수정·삭제** — 패널 내에서 직접 편집 가능
- **체크리스트 노트** — 항목별 체크/해제 지원
- **자동 저장** — 뒤로가기·ESC·패널 닫기 시 변경사항 자동 저장
- **되돌리기** — 수정 중 마지막 저장 상태로 즉시 복원
- **링크 자동 인식** — 노트 내 URL 클릭 시 브라우저 오픈
- **클립보드 복사** — 목록 카드 호버 📋 / 편집기 버튼으로 제목+내용 복사
- **보관함** — 노트를 보관함으로 이동, 목록 조회 및 보관 해제
- **휴지통** — 삭제 노트를 휴지통으로 이동, 복원 / 영구 삭제 / 휴지통 비우기
- **라벨 관리** — 사이드바에 라벨 목록 표시 및 클릭 필터링, 편집기에서 노트에 라벨 할당, 라벨 추가·이름변경·삭제
- **폰트 설정** — 목록 제목/내용, 편집기 제목/본문별 폰트 종류·크기 개별 설정
- **자동 업데이트** — GitHub Releases에서 새 버전 감지 시 알림, 원클릭 다운로드·설치
- **내보내기·공유** — Markdown / TXT / PNG / PDF / 한글(.hwpx) / Word(.docx) 저장, 이메일·카카오톡 공유
- **내 메일로 보내기** — 설정에 내 메일 주소 저장 후 원클릭 전송
- **번역 새 노트** — MyMemory API로 노트를 번역하여 새 노트 생성
- **자동 시작** — macOS LaunchAgent / Windows 레지스트리 등록·해제
- **다국어 지원** — 한국어·영어·일본어, 사이드바에서 즉시 전환 가능
- **한국어 IME 최적화** — macOS 한글 입력 첫 글자 자소 분리 현상 수정

## 인증 방식

keeptray은 **Playwright Chromium**을 사용해 Google 계정에 로그인합니다.

1. 앱 실행 → "Google로 로그인" 버튼 클릭
2. Chromium 창이 자동으로 열립니다
3. Google 계정으로 로그인하면 인증이 자동으로 완료됩니다
4. 이후 실행부터는 저장된 세션이 자동으로 복원됩니다 (재로그인 불필요)

> 인증 쿠키(SAPISID)는 macOS Keychain / Windows 자격 증명 관리자와 `~/.config/keeptray/session.json`에 저장됩니다.  
> Google 앱 비밀번호나 별도 API 키는 필요하지 않습니다.

## 설치

### macOS (.dmg)

1. [Releases](../../releases) 에서 `keeptray-[버전].dmg` 다운로드
2. DMG를 열고 `keeptray.app`을 Applications 폴더로 드래그

#### 최초 실행 시 필수 명령어

macOS는 인터넷에서 다운로드한 앱을 **Gatekeeper**로 차단합니다. Apple Developer 인증서 없이 배포된 앱은 별도의 허용 절차가 필요합니다.

```bash
xattr -rd com.apple.quarantine /Applications/keeptray.app && open /Applications/keeptray.app
```

이 명령은 **최초 1회**만 실행하면 되며, 이후에는 평소처럼 앱을 클릭해서 실행할 수 있습니다.

### Windows (.zip)

1. [Releases](../../releases) 에서 `keeptray-[버전]-win.zip` 다운로드
2. ZIP을 원하는 폴더에 압축 해제
3. `keeptray\keeptray.exe` 실행

#### Windows 첫 실행

- **Chromium 자동 설치**: 첫 실행 시 Google 로그인에 필요한 Chromium 브라우저를 자동으로 다운로드합니다 (약 150MB, 1회만).  
  다운로드 경로: `%LOCALAPPDATA%\keeptray\ms-playwright`
- **Windows Defender**: 서명되지 않은 앱으로 경고가 뜰 수 있습니다. "추가 정보 → 실행"을 클릭하면 됩니다.

## 개발 환경 실행

```bash
# 1. 의존성 설치
pip install -e .

# 2. Playwright Chromium 설치 (최초 1회)
python -m playwright install chromium

# 3. 실행
python -m keeptray
```

## 배포 빌드

### macOS (.dmg)

```bash
# PyInstaller + 코드서명 + DMG 생성
bash build_dmg.sh
# → dist/keeptray-[버전].dmg
```

> **빌드 요구사항**: `pip install pyinstaller pyqt6==6.7.1`  
> codesign은 ad-hoc 서명(`-`)을 사용하므로 Apple Developer 계정 불필요.

### Windows (.zip)

```powershell
# PyInstaller + ZIP 패키징
python -m PyInstaller keeptray_win.spec --noconfirm
# → dist/keeptray/ 폴더 → ZIP으로 압축
```

> **빌드 요구사항**: `pip install pyinstaller pyqt6==6.7.1`

## 기술 스택

| 구분 | 라이브러리 | 플랫폼 | 설명 |
|------|-----------|--------|------|
| GUI | [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) 6.7.1 | 공통 | Qt6 기반 크로스플랫폼 GUI 프레임워크 |
| 트레이 (macOS) | [rumps](https://github.com/jaredks/rumps) | macOS | macOS 메뉴바 앱 Python 래퍼 |
| 트레이 (Windows) | [pystray](https://github.com/moses-palmer/pystray) + [Pillow](https://python-pillow.org/) | Windows | Windows 시스템 트레이 아이콘 |
| macOS 네이티브 | [PyObjC](https://pyobjc.readthedocs.io/) | macOS | Objective-C/AppKit API Python 바인딩 |
| Keep API | [gkeepapi](https://github.com/kiwiz/gkeepapi) | 공통 | 비공식 Google Keep API 클라이언트 |
| 브라우저 로그인 | [Playwright](https://playwright.dev/python/) | 공통 | Chromium 제어로 Google 계정 로그인 처리 |
| 세션 저장 | [keyring](https://github.com/jaraco/keyring) | 공통 | macOS Keychain / Windows 자격 증명 관리자 |
| 문서 저장 | [python-docx](https://python-docx.readthedocs.io/), [python-hwpx](https://github.com/airmang/python-hwpx) | 공통 | Word(.docx) / 한글(.hwpx) 내보내기 |
| 패키징 | [PyInstaller](https://pyinstaller.org/) 6.x | 공통 | Python 앱을 단일 실행 파일로 패키징 |
| 다국어 | [gettext](https://docs.python.org/3/library/gettext.html) | 공통 | `.po`/`.mo` 기반 번역, 런타임 언어 전환 |

## 번역 기여

keeptray은 현재 한국어·영어·일본어를 지원합니다. 새로운 언어를 추가하거나 기존 번역을 개선하고 싶으신 분은 언제든지 기여해주세요!

- 번역 파일 위치: `i18n/{언어코드}/LC_MESSAGES/keeptray.po`
- 자세한 기여 방법은 [CONTRIBUTING_TRANSLATION.md](CONTRIBUTING_TRANSLATION.md)를 참고해주세요

기여자분의 이름은 [CONTRIBUTORS.md](CONTRIBUTORS.md)에 기록됩니다. 🙏

## 라이선스

[GNU GPL v3](LICENSE)
