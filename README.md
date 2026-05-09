# keep4mac

Google Keep macOS 메뉴바 앱. 트레이 아이콘을 클릭하면 Keep 노트를 바로 조회·작성·수정·삭제할 수 있습니다.

## 주요 기능

- **메뉴바 상주** — 앱이 Dock 없이 메뉴바 아이콘으로 실행됩니다
- **트레이 직접 클릭** — 아이콘 클릭 시 노트 목록 패널이 즉시 열립니다
- **노트 목록 조회** — 최신 노트 목록을 카드 형태로 표시, 이미지 썸네일 지원
- **노트 작성·수정·삭제** — 패널 내에서 직접 편집 가능
- **링크 자동 인식** — 노트 내 URL 클릭 시 브라우저 오픈
- **로그인 자동 시작** — 사이드바 토글로 macOS LaunchAgent 등록/해제
- **Google 앱 비밀번호 인증** — 인증 정보는 macOS Keychain에만 저장

## 설치

1. [Releases](../../releases) 에서 `keep4mac-x.x.x.dmg` 다운로드
2. DMG를 열고 `keep4mac.app`을 Applications 폴더로 드래그
3. 터미널에서 Gatekeeper 격리 해제:
   ```bash
   xattr -cr /Applications/keep4mac.app
   ```
4. Launchpad 또는 Finder에서 실행

## Google 앱 비밀번호 발급

keep4mac은 Google 앱 비밀번호를 사용합니다.

1. [Google 계정 보안 설정](https://myaccount.google.com/security) 접속
2. 2단계 인증 활성화 (미활성화 시 앱 비밀번호 항목 미표시)
3. **앱 비밀번호** → "앱 선택: 기타" → `keep4mac` 입력 → 생성
4. 생성된 16자리 비밀번호를 앱 첫 실행 시 입력

> 인증 정보는 macOS Keychain에만 저장되며 코드/파일에 기록되지 않습니다.

## 개발 환경 실행

```bash
# 1. conda 환경 또는 가상환경에 의존성 설치
pip install -e ".[dev]"

# 2. 실행
python -m keep4mac
```

## 배포 빌드 (.dmg)

```bash
# PyInstaller + 코드서명 + DMG 생성 (all-in-one)
bash build_dmg.sh
# → dist/keep4mac-0.1.0.dmg
```

> **참고**: 빌드 환경에 `pip install pyinstaller pyqt6==6.7.1` 필요.  
> codesign은 ad-hoc 서명(`-`)을 사용하므로 Apple Developer 계정 불필요.

## 기술 스택

| 구분 | 라이브러리 |
|------|-----------|
| GUI | PyQt6 6.7.1 |
| 메뉴바 | rumps + PyObjC |
| Keep API | gkeepapi |
| 인증 | keyring (macOS Keychain) |
| 패키징 | PyInstaller 6.x |

## 개발 상태

| 기능 | 상태 |
|------|------|
| 메뉴바 상주 + 트레이 아이콘 | ✅ 완료 |
| 트레이 직접 클릭으로 패널 열기 | ✅ 완료 |
| 노트 목록 조회 (이미지 포함) | ✅ 완료 |
| 노트 작성 / 수정 / 삭제 | ✅ 완료 |
| 링크 자동 인식 | ✅ 완료 |
| 로그인 자동 시작 (LaunchAgent) | ✅ 완료 |
| DMG 배포 빌드 | ✅ 완료 |
| 클립보드 복사 버튼 | 🔲 예정 |
| 백그라운드 자동 동기화 | 🔲 예정 |
