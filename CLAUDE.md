# keeptray

## 프로젝트 개요
<!-- 프로젝트 설명을 여기에 작성하세요 -->

## 컨텍스트 앵커
- intent: macOS 메뉴바 Google Keep 앱 — 기능 완성 및 배포
- changes_made: v0.1.44 기준 — #61 Windows 지원(pystray, tray_win.py, autostart winreg, panel.py objc lazy import, keeptray_win.spec, build_exe.ps1, release.yml Windows job)
- decisions: app.py에서 플랫폼 분기(darwin→rumps, 기타→pystray+qt_app.exec()), pystray 콜백은 SimpleQueue+QTimer(50ms)로 메인 스레드 전달
- next_steps: #60 노트 목록 정렬, Windows 실제 빌드 테스트
