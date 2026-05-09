# keep4mac

Google Keep macOS 메뉴바 앱. 트레이 아이콘을 클릭하면 Keep 노트를 바로 조회·작성·수정·삭제할 수 있습니다.

## 주요 기능

- **메뉴바 상주** — 앱이 Dock 없이 메뉴바 아이콘으로 실행됩니다
- **트레이 직접 클릭** — 아이콘 클릭 시 노트 목록 패널이 즉시 열립니다
- **노트 목록 조회** — 최신 노트 목록을 카드 형태로 표시, 이미지 썸네일 지원
- **노트 작성·수정·삭제** — 패널 내에서 직접 편집 가능
- **체크리스트 노트** — 항목별 체크/해제 지원
- **링크 자동 인식** — 노트 내 URL 클릭 시 브라우저 오픈
- **클립보드 복사** — 노트 카드 호버 시 📋 버튼으로 제목+내용 복사
- **로그인 자동 시작** — 사이드바 토글로 macOS LaunchAgent 등록/해제

## 인증 방식

keep4mac은 **Playwright Chromium**을 사용해 Google 계정에 로그인합니다.

1. 앱 실행 → "Google로 로그인" 버튼 클릭
2. Chromium 창이 자동으로 열립니다
3. Google 계정으로 로그인하면 인증이 자동으로 완료됩니다
4. 이후 실행부터는 저장된 세션이 자동으로 복원됩니다 (재로그인 불필요)

> 인증 쿠키(SAPISID)는 macOS Keychain과 `~/.config/keep4mac/session.json`에 저장됩니다.  
> Google 앱 비밀번호나 별도 API 키는 필요하지 않습니다.

## 설치 (DMG)

1. [Releases](../../releases) 에서 `keep4mac-x.x.x.dmg` 다운로드
2. DMG를 열고 `keep4mac.app`을 Applications 폴더로 드래그
3. 터미널에서 아래 명령어 실행:
   ```bash
   xattr -rd com.apple.quarantine /Applications/keep4mac.app && open /Applications/keep4mac.app
   ```

## 개발 환경 실행

```bash
# 1. 의존성 설치
pip install -e .

# 2. Playwright Chromium 설치 (최초 1회)
python -m playwright install chromium

# 3. 실행
python -m keep4mac
```

## 배포 빌드 (.dmg)

```bash
# PyInstaller + 코드서명 + DMG 생성
bash build_dmg.sh
# → dist/keep4mac-0.1.0.dmg
```

> **빌드 요구사항**: `pip install pyinstaller pyqt6==6.7.1 playwright`  
> codesign은 ad-hoc 서명(`-`)을 사용하므로 Apple Developer 계정 불필요.  
> DMG에는 Playwright Chromium이 포함되지 않으므로, 첫 실행 시 Chromium 다운로드가 필요합니다.

## 기술 스택

| 구분 | 라이브러리 |
|------|-----------|
| GUI | PyQt6 6.7.1 |
| 메뉴바 | rumps + PyObjC |
| Keep API | gkeepapi (SAPISIDHASH 인증) |
| 브라우저 로그인 | Playwright (Chromium) |
| 세션 저장 | keyring (macOS Keychain) |
| 패키징 | PyInstaller 6.x |

## 개발 상태

| 기능 | 상태 |
|------|------|
| 메뉴바 상주 + 트레이 아이콘 | ✅ 완료 |
| 트레이 직접 클릭으로 패널 열기 | ✅ 완료 |
| Playwright 브라우저 로그인 | ✅ 완료 |
| 노트 목록 조회 (이미지 포함) | ✅ 완료 |
| 노트 작성 / 수정 / 삭제 | ✅ 완료 |
| 체크리스트 노트 | ✅ 완료 |
| 링크 자동 인식 | ✅ 완료 |
| 로그인 자동 시작 (LaunchAgent) | ✅ 완료 |
| DMG 배포 빌드 | ✅ 완료 |
| 클립보드 복사 버튼 | ✅ 완료 |
| 백그라운드 자동 동기화 | ➖ 구현 안 함 |
