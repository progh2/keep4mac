# 번역 기여 가이드 / Translation Contribution Guide

keeptray은 gettext 기반 다국어를 지원합니다. 새로운 언어를 추가하거나 기존 번역을 개선하려면 아래 절차를 따르세요.

keeptray uses gettext-based i18n. Follow the steps below to add a new language or improve an existing translation.

---

## 파일 구조 / File Structure

```
i18n/
├── ko/LC_MESSAGES/keeptray.po   # 한국어
├── en/LC_MESSAGES/keeptray.po   # English (empty msgstr — falls back to msgid)
└── ja/LC_MESSAGES/keeptray.po   # 日本語
```

각 언어 코드는 ISO 639-1 두 글자 코드입니다 (예: `fr`, `de`, `zh`).

---

## 새 언어 추가 / Adding a New Language

1. `en/LC_MESSAGES/keeptray.po`를 복사해 새 언어 폴더에 붙여넣습니다.
   ```
   mkdir -p i18n/fr/LC_MESSAGES
   cp i18n/en/LC_MESSAGES/keeptray.po i18n/fr/LC_MESSAGES/keeptray.po
   ```

2. `keeptray.po` 파일 헤더의 `Language:` 값을 바꿉니다.
   ```
   "Language: fr\n"
   ```

3. 각 `msgid` 아래 `msgstr ""`에 번역을 채워 넣습니다.
   ```po
   msgid "New Note"
   msgstr "Nouvelle note"
   ```

4. [Poedit](https://poedit.net/) 같은 .po 편집기를 사용해도 됩니다.

5. Pull Request를 보내 주세요! `.mo` 파일은 CI에서 자동으로 컴파일됩니다.

---

## 번역 문자열 목록 / Translatable Strings

| msgid | 설명 |
|-------|------|
| `New Note` | 사이드바 새 노트 버튼 |
| `Sync` | 사이드바 동기화 버튼 |
| `Web Keep` | 사이드바 웹 Keep 버튼 |
| `🚀\nAutostart` | 사이드바 자동시작 버튼 (이모지 포함) |
| `Autostart enabled (click to disable)` | 자동시작 툴팁 (활성) |
| `Start at login (click to enable)` | 자동시작 툴팁 (비활성) |
| `About` | 사이드바 정보 버튼 |
| `Logout` | 사이드바 로그아웃 버튼 |
| `Quit` | 사이드바 종료 버튼 |
| `Google Keep Menu Bar App` | 로그인 화면 부제목 |
| `Sign in with Google Account` | 로그인 카드 제목 |
| `Click the button to open a browser.\nSign in with your Google account to connect automatically.` | 로그인 안내 (줄바꿈 포함) |
| `Sign in with Google` | 로그인 버튼 |
| `Opening browser…` | 브라우저 열기 중 버튼 텍스트 |
| `🔍  Search…` | 검색창 placeholder |
| `No notes` | 노트 없을 때 안내 |
| `📌  Pinned` | 고정 노트 섹션 헤더 |
| `Notes` | 일반 노트 섹션 헤더 |
| `Copy to clipboard` | 복사 버튼 툴팁 |
| `Edit Note` | 에디터 헤더 |
| `Delete` | 삭제 버튼 툴팁 |
| `Title` | 제목 입력 placeholder |
| `Enter note content…` | 내용 입력 placeholder |
| `🗑  Delete Image` | 이미지 삭제 버튼 |
| `🔗 Links` | 링크 섹션 헤더 |
| `Pin / Unpin` | 핀 고정 툴팁 |
| `Save` | 저장 버튼 |
| `Loading image…` | 이미지 로딩 중 텍스트 |
| `About keeptray` | About 다이얼로그 제목 |
| `Google Keep Menu Bar App` | About 다이얼로그 설명 |
| `Version` | 버전 레이블 |
| `Made by` | 만든 이 레이블 |
| `Close` | 닫기 버튼 |

---

## 주의사항 / Notes

- 이모지가 포함된 msgid는 이모지를 그대로 유지하세요.
- `\n`이 포함된 문자열은 줄바꿈을 유지해야 합니다.
- `.mo` 파일은 커밋하지 않아도 됩니다 (CI 자동 생성).
