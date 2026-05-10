#!/usr/bin/env bash
# keep4mac .app + .dmg 빌드 스크립트
set -e

APP_NAME="keep4mac"
VERSION="0.1.42"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
TMP_DMG="/tmp/${APP_NAME}_tmp.dmg"
MOUNT_DIR="/tmp/${APP_NAME}_mount"

echo "▶ 이전 빌드 정리..."
rm -rf build dist

echo "▶ .app 빌드 (PyInstaller)..."
python3 -m PyInstaller keep4mac.spec --noconfirm 2>&1 | tail -5

APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
    echo "✗ 빌드 실패: $APP_PATH 가 없습니다."
    exit 1
fi

echo "▶ Qt 플러그인 교체 (pip PyQt6)..."
PYQT6_PLUGINS=$(python3 -c "import PyQt6, os; print(os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins'))")
BUNDLE_PLUGINS="${APP_PATH}/Contents/Frameworks/PyQt6/Qt6/plugins"
for plugin_dir in platforms styles imageformats; do
    if [ -d "${PYQT6_PLUGINS}/${plugin_dir}" ]; then
        rm -rf "${BUNDLE_PLUGINS}/${plugin_dir}"
        cp -r "${PYQT6_PLUGINS}/${plugin_dir}" "${BUNDLE_PLUGINS}/${plugin_dir}"
        echo "  ✓ ${plugin_dir}"
    fi
done

echo "▶ dist-info → Contents/Resources 이동 (codesign 충돌 방지)..."
FRAMEWORKS="${APP_PATH}/Contents/Frameworks"
RESOURCES="${APP_PATH}/Contents/Resources"
find "$FRAMEWORKS" -maxdepth 1 -name "*.dist-info" | while read d; do
    name=$(basename "$d")
    if [ ! -d "$RESOURCES/$name" ]; then
        cp -rL "$d" "$RESOURCES/$name"   # Resources에 없는 경우만 복사
    fi
    rm -rf "$d"   # Frameworks의 symlink(또는 실제 디렉토리) 삭제
    echo "  ✓ $name"
done

echo "▶ 앱 서명 (ad-hoc)..."
find "${APP_PATH}" \( -name "*.dylib" -o -name "*.so" \) | while read f; do
    codesign --force --sign - "$f" 2>/dev/null
done
codesign --force --sign - --entitlements entitlements.plist "${APP_PATH}" 2>&1
echo "  ✓ 서명 완료"

echo "▶ DMG 생성..."
MOUNT_DIR="/tmp/${APP_NAME}_work_$$"
rm -f "dist/${DMG_NAME}" "$TMP_DMG"

# 임시 읽기-쓰기 이미지 생성
hdiutil create -size 700m -fs HFS+ -volname "$APP_NAME" "$TMP_DMG" -quiet

# 고유한 임시 경로에 마운트 (기존 /Volumes/keep4mac 충돌 방지)
mkdir -p "$MOUNT_DIR"
hdiutil attach "$TMP_DMG" -mountpoint "$MOUNT_DIR" -nobrowse -quiet
echo "  마운트: $MOUNT_DIR"

# .app 드래그 설치 + 안내 문서
ditto "$APP_PATH" "$MOUNT_DIR/keep4mac.app"
ln -s /Applications "$MOUNT_DIR/Applications"
cp "docs/install_guide.txt" "$MOUNT_DIR/꼭 읽어주세요.txt"

# 마운트 해제
hdiutil detach "$MOUNT_DIR" -quiet
rm -rf "$MOUNT_DIR"

# 압축 DMG로 변환
hdiutil convert "$TMP_DMG" -format UDZO -o "dist/${DMG_NAME}" -quiet
rm -f "$TMP_DMG"

echo "✓ 완료: dist/${DMG_NAME}"
echo "  크기: $(du -sh "dist/${DMG_NAME}" | cut -f1)"
