# keep4mac

Google Keep macOS 메뉴바 앱. 트레이 아이콘에서 Keep 노트를 바로 조회·작성·복사할 수 있습니다.

## 요구사항

- macOS 12 Monterey 이상
- Python 3.11+
- Google 계정 (2단계 인증 활성화 필요)

## 설치 및 실행

```bash
# 1. 가상환경 생성
python3 -m venv .venv
source .venv/bin/activate

# 2. 의존성 설치
pip install -e .

# 3. 실행
python -m keep4mac
```

## Google 앱 비밀번호 발급

keep4mac은 Google 앱 비밀번호를 사용합니다.

1. [Google 계정 보안 설정](https://myaccount.google.com/security) 접속
2. 2단계 인증 활성화 (미활성화 시 앱 비밀번호 항목 미표시)
3. **앱 비밀번호** → "앱 선택: 기타" → `keep4mac` 입력 → 생성
4. 생성된 16자리 비밀번호를 앱 첫 실행 시 입력

> 인증 정보는 macOS Keychain에만 저장되며 코드/파일에 기록되지 않습니다.

## 빌드 (.app 번들)

```bash
pip install py2app
python setup.py py2app
# dist/keep4mac.app 생성
```

## 개발 상태

| Phase | 내용 | 상태 |
|-------|------|------|
| 1 | 프로젝트 환경 설정 | ✅ 완료 |
| 2 | Google Keep API 연동 | 🔲 예정 |
| 3 | 메뉴바 트레이 | 🔲 예정 |
| 4 | 노트 목록 GUI | 🔲 예정 |
| 5 | 노트 편집 | 🔲 예정 |
| 6 | 검색 + 복사 | 🔲 예정 |
| 7 | 백그라운드 동기화 | 🔲 예정 |
| 8 | 앱 패키징 | 🔲 예정 |
