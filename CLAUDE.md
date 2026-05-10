# keep4mac

## 프로젝트 개요
<!-- 프로젝트 설명을 여기에 작성하세요 -->

## 컨텍스트 앵커
- intent: macOS 메뉴바 Google Keep 앱 — 기능 완성 및 배포
- changes_made: v0.1.42 기준 — #38 플로팅 독립 윈도우(드래그 바, setHidesOnDeactivate_(False), 위치 저장/복원, toggle_visibility), settings.py에 window_pos 추가, 패널 높이 608px
- decisions: _DragBar(28px) 상단 배치 → QVBoxLayout 구조 변경, hideEvent에서 위치 저장, 트레이 클릭 toggle_visibility로 전환
- next_steps: #37 UI 아이콘 스타일 통일, #42 macOS HIG 적용
