# keep4mac

Google Keep macOS 메뉴바 앱. 트레이 아이콘을 클릭하면 Keep 노트를 바로 조회·작성·수정·삭제할 수 있습니다.

## 주요 기능

- **메뉴바 상주** — 앱이 Dock 없이 메뉴바 아이콘으로 실행됩니다
- **트레이 직접 클릭** — 아이콘 클릭 시 노트 목록 패널이 즉시 열립니다
- **노트 목록 조회** — 최신 노트 목록을 카드 형태로 표시, 이미지 썸네일 지원
- **노트 작성·수정·삭제** — 패널 내에서 직접 편집 가능
- **체크리스트 노트** — 항목별 체크/해제 지원
- **자동 저장** — 뒤로가기·ESC·패널 닫기 시 변경사항 자동 저장
- **되돌리기** — 수정 중 마지막 저장 상태로 즉시 복원
- **링크 자동 인식** — 노트 내 URL 클릭 시 브라우저 오픈
- **클립보드 복사** — 목록 카드 호버 📋 / 편집기 버튼으로 제목+내용 복사
- **내보내기·공유** — Markdown / TXT / PNG / PDF / 한글(.hwpx) / Word(.docx) 저장, 이메일·카카오톡 공유
- **내 메일로 보내기** — 설정에 내 메일 주소 저장 후 원클릭 전송
- **번역 새 노트** — MyMemory API로 노트를 번역하여 새 노트 생성
- **로그인 자동 시작** — 사이드바 토글로 macOS LaunchAgent 등록/해제
- **다국어 지원** — 한국어·영어·일본어, 사이드바에서 즉시 전환 가능
- **한국어 IME 최적화** — macOS 한글 입력 첫 글자 자소 분리 현상 수정

## 인증 방식

keep4mac은 **Playwright Chromium**을 사용해 Google 계정에 로그인합니다.

1. 앱 실행 → "Google로 로그인" 버튼 클릭
2. Chromium 창이 자동으로 열립니다
3. Google 계정으로 로그인하면 인증이 자동으로 완료됩니다
4. 이후 실행부터는 저장된 세션이 자동으로 복원됩니다 (재로그인 불필요)

> 인증 쿠키(SAPISID)는 macOS Keychain과 `~/.config/keep4mac/session.json`에 저장됩니다.  
> Google 앱 비밀번호나 별도 API 키는 필요하지 않습니다.

## 설치 (DMG)

1. [Releases](../../releases) 에서 `keep4mac-[버전].dmg` 다운로드
2. DMG를 열고 `keep4mac.app`을 Applications 폴더로 드래그

### 최초 실행 시 필수 명령어

macOS는 인터넷에서 다운로드한 앱을 **Gatekeeper**로 차단합니다. Apple Developer 인증서 없이 배포된 앱은 별도의 허용 절차가 필요합니다. 아래 명령어를 터미널에서 실행해 격리 속성을 해제한 뒤 앱을 열어주세요.

```bash
xattr -rd com.apple.quarantine /Applications/keep4mac.app && open /Applications/keep4mac.app
```

- `xattr -rd com.apple.quarantine` : macOS가 붙여놓은 격리(quarantine) 플래그를 제거합니다
- 이 명령은 **최초 1회**만 실행하면 되며, 이후에는 평소처럼 앱을 클릭해서 실행할 수 있습니다

## 개발 환경 실행

```bash
# 1. 의존성 설치
pip install -e .

# 2. Playwright Chromium 설치 (최초 1회)
#    keep4mac은 Google 로그인에 Playwright Chromium을 사용합니다.
#    앱 실행 전에 반드시 한 번 실행해야 합니다.
python -m playwright install chromium

# 3. 실행
python -m keep4mac
```

## 배포 빌드 (.dmg)

```bash
# PyInstaller + 코드서명 + DMG 생성
bash build_dmg.sh
# → dist/keep4mac-[버전].dmg
```

> **빌드 요구사항**: `pip install pyinstaller pyqt6==6.7.1 playwright`  
> codesign은 ad-hoc 서명(`-`)을 사용하므로 Apple Developer 계정 불필요.  
> DMG에는 Playwright Chromium이 포함되지 않으므로, 첫 실행 시 Chromium 다운로드가 필요합니다.

## 기술 스택

| 구분 | 라이브러리 | 설명 |
|------|-----------|------|
| GUI | [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) 6.7.1 | Qt6 기반 크로스플랫폼 GUI 프레임워크. 노트 목록·에디터·로그인 등 모든 UI에 사용 |
| 메뉴바 | [rumps](https://github.com/jaredks/rumps) | macOS 메뉴바 앱을 간편하게 만들어주는 Python 래퍼 |
| macOS 네이티브 | [PyObjC](https://pyobjc.readthedocs.io/) | Objective-C/AppKit API를 Python에서 직접 호출. 트레이 클릭·아이콘·CALayer에 사용 |
| Keep API | [gkeepapi](https://github.com/kiwiz/gkeepapi) | 비공식 Google Keep API 클라이언트. SAPISIDHASH 인증 방식으로 연동 |
| 브라우저 로그인 | [Playwright](https://playwright.dev/python/) | Chromium 제어로 Google 계정 로그인 처리. 자동화된 쿠키 추출에 사용 |
| 세션 저장 | [keyring](https://github.com/jaraco/keyring) | macOS Keychain에 인증 정보를 안전하게 저장·불러오기 |
| 문서 저장 | [python-docx](https://python-docx.readthedocs.io/), [python-hwpx](https://github.com/airmang/python-hwpx) | Word(.docx) 및 한글(.hwpx) 형식 내보내기 |
| 패키징 | [PyInstaller](https://pyinstaller.org/) 6.x | Python 앱을 단일 `.app` 번들로 패키징 |
| 다국어 | [gettext](https://docs.python.org/3/library/gettext.html) (표준 라이브러리) | `.po`/`.mo` 파일 기반 번역. 시스템 언어 자동 감지 및 런타임 언어 전환 지원 |

## 번역 기여

keep4mac은 현재 한국어·영어·일본어를 지원합니다. 새로운 언어를 추가하거나 기존 번역을 개선하고 싶으신 분은 언제든지 기여해주세요!

- 번역 파일 위치: `i18n/{언어코드}/LC_MESSAGES/keep4mac.po`
- 자세한 기여 방법은 [CONTRIBUTING_TRANSLATION.md](CONTRIBUTING_TRANSLATION.md)를 참고해주세요

기여자분의 이름은 [CONTRIBUTORS.md](CONTRIBUTORS.md)에 기록됩니다. 🙏

## 라이선스

[GNU GPL v3](LICENSE)
