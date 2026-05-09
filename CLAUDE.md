# keep4mac

## 프로젝트 개요
<!-- 프로젝트 설명을 여기에 작성하세요 -->

## 컨텍스트 앵커
- intent: macOS 메뉴바 Google Keep 앱 — 기능 완성 및 배포
- changes_made: ghost text 버그 수정(노트 목록 스크롤), DMG 빌드 완성 (pip PyQt6 플러그인 후처리 교체 방식)
- decisions: PyInstaller hook이 Qt5 플러그인 자동 수집 → 빌드 후 pip PyQt6 플러그인(/opt/anaconda3/lib/python3.13/site-packages/PyQt6/Qt6/plugins)으로 덮어쓰는 방식 사용
- next_steps: 추가 기능 요청 대기
