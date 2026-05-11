# keeptray

## 프로젝트 개요

macOS 메뉴바 + Windows 시스템 트레이에서 Google Keep 노트를 조회·편집하는 크로스플랫폼 데스크탑 앱.
PyQt6 UI, rumps(macOS)/pystray(Windows) 트레이, gkeepapi 비공식 API, Playwright 인증.

## 하네스

### 작업 사이클

"처리해줘" = 이슈 등록 → 코드 수정 → 커밋 → 태그 푸시 → 자동 빌드까지 전부.  
별도 지시 없으면 이 순서로 끝까지 진행한다. "구현 포기" / "다음에" 라고 명시할 때만 보류.

```
이슈 등록 → 수정 → 커밋 → git tag vX.X.X → git push origin vX.X.X
                                               ↓
                                     GitHub Actions 자동 빌드
                                     (macOS DMG + Windows ZIP)
```

- 버전은 pre-commit 훅이 자동 증가 → 수동 지정 불필요
- 이슈 번호는 커밋 메시지에 `close #XX` 형태로 포함

### 문서 동기화 (작업 완료 후 판단)

| 변경 유형 | README | PRD |
|-----------|--------|-----|
| 기능 추가·변경 | 관련 섹션 업데이트 | 해당 항목 업데이트 |
| 동작 방식·API 변경 | 필요 시 업데이트 | 업데이트 |
| 단순 버그 수정 | 스킵 | 스킵 |
| 리팩터링 | 스킵 | 스킵 |

### 릴리즈 전 체크리스트

**새 라이브러리 추가 또는 기능 변경이 있을 때만** 전체 확인:

- [ ] 새 라이브러리 라이선스가 GPL v3 호환인지
- [ ] `keeptray.spec` / `keeptray_win.spec` hiddenimports에 추가됐는지
- [ ] `collect_data_files()`가 필요한 패키지인지 (템플릿·인증서 등 데이터 파일 포함 여부)
- [ ] 비공식 API 사용·개인정보 처리 방식 변경이 있는지

**순수 버그 수정일 때:**

- [ ] README·PRD 업데이트가 필요한 변경인지만 확인

### 플랫폼 동시 고려

모든 수정에서 아래를 확인한다:

- `sys.platform == "darwin"` 분기가 필요한지
- Qt 스타일시트가 Windows에서 부모 스타일을 상속해 검은 화면이 되는지  
  → `QInputDialog` 대신 커스텀 `QDialog` + 명시적 배경색 사용
- PyInstaller frozen 환경에서 import 경로·동작이 달라지는지
- `keeptray_win.spec` hiddenimports·datas 갱신이 필요한지

### PyInstaller 패턴 (이 프로젝트 전용)

- frozen 앱 여부: `getattr(sys, "frozen", False)`
- Playwright 드라이버: `compute_driver_executable()` (≥1.45) → `get_driver_executable()` (구버전) fallback
- `PLAYWRIGHT_BROWSERS_PATH`: `__main__.py` 시작 직후 가장 먼저 설정 (BNZ 임시경로 방지)
- 새 라이브러리 추가 시: hiddenimports + `collect_data_files()` 동시 추가

### 스크린샷 버그 처리

1. 이미지에서 에러 메시지·화면 상태 파악
2. 소스 위치 찾기
3. GitHub 이슈 등록 (이미지는 CLI 미지원 → 에러 내용을 텍스트로 상세 기록)
4. 수정 → 릴리즈까지 한 번에

### 커뮤니케이션 패턴

| 지시 | 의미 |
|------|------|
| "처리해줘" | 이슈 등록 + 구현 + 릴리즈 전부 |
| "이슈 등록해줘" | 등록만, 구현은 별도 지시 대기 |
| "릴리즈해줘" | 커밋 + 태그 + 푸시 |
| "점검해줘" | 분석 결과 먼저 보고, 수정은 확인 후 |
| "구현 포기" / "다음에" | 해당 작업 보류 |

## 컨텍스트 앵커
- intent: macOS/Windows 데스크탑 트레이 Google Keep 앱 — 크로스플랫폼 안정화 및 기능 완성
- changes_made: v0.1.56 기준 (2026-05-11) — 프로젝트 rename keep4mac→keeptray(#64), Windows Playwright 브라우저 영구 경로 고정(PLAYWRIGHT_BROWSERS_PATH), Windows hwpx/docx 크래시 수정(hiddenimports+try/except), DMG 빌드 안정화(rsync+동적 크기), QInputDialog 검은 화면 수정(커스텀 QDialog), 누락 라이브러리 전수 보완(gkeepapi/certifi/requests 등)
- decisions: app.py 플랫폼 분기(darwin→rumps, 기타→pystray+qt_app.exec()), pystray 콜백 SimpleQueue+QTimer(50ms) 메인 스레드 전달, Playwright 브라우저 경로 %LOCALAPPDATA%\keeptray\ms-playwright로 고정(PyInstaller BNZ 임시경로 방지), win spec에 collect_data_files(docx/hwpx/certifi) 포함
- next_steps: #60 노트 목록 정렬 구현, Windows 사용자 피드백 수집
