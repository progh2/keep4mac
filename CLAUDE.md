# keeptray

## 프로젝트 개요
<!-- 프로젝트 설명을 여기에 작성하세요 -->

## 컨텍스트 앵커
- intent: macOS/Windows 데스크탑 트레이 Google Keep 앱 — 크로스플랫폼 안정화 및 기능 완성
- changes_made: v0.1.56 기준 (2026-05-11) — 프로젝트 rename keep4mac→keeptray(#64), Windows Playwright 브라우저 영구 경로 고정(PLAYWRIGHT_BROWSERS_PATH), Windows hwpx/docx 크래시 수정(hiddenimports+try/except), DMG 빌드 안정화(rsync+동적 크기), QInputDialog 검은 화면 수정(커스텀 QDialog), 누락 라이브러리 전수 보완(gkeepapi/certifi/requests 등)
- decisions: app.py 플랫폼 분기(darwin→rumps, 기타→pystray+qt_app.exec()), pystray 콜백 SimpleQueue+QTimer(50ms) 메인 스레드 전달, Playwright 브라우저 경로 %LOCALAPPDATA%\keeptray\ms-playwright로 고정(PyInstaller BNZ 임시경로 방지), win spec에 collect_data_files(docx/hwpx/certifi) 포함
- next_steps: #60 노트 목록 정렬 구현, Windows 사용자 피드백 수집
