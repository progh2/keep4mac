#!/bin/bash
clear
APP_PATH="/Applications/keep4mac.app"

echo "=============================="
echo "  keep4mac 설치 도우미"
echo "=============================="
echo ""

if [ ! -d "$APP_PATH" ]; then
    echo "❌ /Applications/keep4mac.app 을 찾을 수 없습니다."
    echo ""
    echo "먼저 DMG 창에서 keep4mac.app을"
    echo "오른쪽 Applications 폴더로 드래그한 후"
    echo "이 스크립트를 다시 실행해주세요."
    echo ""
    read -p "엔터를 누르면 종료합니다..."
    exit 1
fi

echo "✓ keep4mac.app 확인"
echo ""
echo "macOS 보안 설정을 해제합니다..."
xattr -cr "$APP_PATH"
echo "✓ 완료!"
echo ""
echo "keep4mac을 실행합니다..."
sleep 1
open "$APP_PATH"
