# keep4mac

## 프로젝트 개요
<!-- 프로젝트 설명을 여기에 작성하세요 -->

## 컨텍스트 앵커
- intent: macOS 메뉴바 Google Keep 앱 — 기능 완성 및 배포
- changes_made: v0.1.40 기준 — HWPX 이미지 삽입(ZIP 직접 조작), 자동저장+되돌리기 버튼, 저장 버튼 제거, 목록 자동 갱신, 한국어 IME 자소 분리 수정(_IMELineEdit/_IMETextEdit), 편집기 📋 복사 버튼, 내 메일 주소 설정(settings.py), 내 메일로 보내기, 메일 제목 형식 통일(keep4mac - {제목}), README·PRD 현행화, v0.1.40 릴리즈
- decisions: HWPX 이미지는 ZIP 직접 조작(python-hwpx add_shape 불충분), 자동저장은 _do_save() 분리+panel.show_near_menubar에서 auto_save_if_needed() 호출, 설정은 ~/.config/keep4mac/settings.json
- next_steps: #37 UI 아이콘 스타일 통일, #38 플로팅 독립 윈도우, #42 macOS HIG 적용
