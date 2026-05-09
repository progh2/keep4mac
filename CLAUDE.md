# keep4mac

## 프로젝트 개요
<!-- 프로젝트 설명을 여기에 작성하세요 -->

## 컨텍스트 앵커
- intent: macOS 메뉴바 Google Keep 앱 기능 완성
- changes_made: 트레이 직접 클릭(#19) + 호버 색상 효과(#20) 완료 — NSImageSymbolConfiguration.configurationWithHierarchicalColor_ 사용
- decisions: imageWithTintColor_ PyObjC 미지원→imageWithSymbolConfiguration_ 사용, setContentTintColor_는 메뉴바에서 검은색 문제
- next_steps: 둥근 모서리(Issue #18), 핀 고정 토글, 앱 배포(dmg)
