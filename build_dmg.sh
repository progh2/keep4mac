#!/usr/bin/env bash
# keeptray .app + .dmg 빌드 스크립트
set -e

APP_NAME="keeptray"
VERSION="0.1.76"
DMG_NAME="${APP_NAME}-${VERSION}.dmg"
TMP_DMG="/tmp/${APP_NAME}_tmp.dmg"
MOUNT_DIR="/tmp/${APP_NAME}_mount"

echo "▶ 이전 빌드 정리..."
rm -rf build dist

echo "▶ .app 빌드 (PyInstaller)..."
python3 -m PyInstaller keeptray.spec --noconfirm 2>&1 | tail -5

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

# 앱 실제 크기 측정 후 여유 포함 용량 산정
APP_SIZE_MB=$(du -sm "$APP_PATH" 2>/dev/null | cut -f1)
DMG_SIZE_MB=$(( APP_SIZE_MB + 200 ))
if [ "$DMG_SIZE_MB" -lt 800 ]; then
    DMG_SIZE_MB=800
fi
echo "  앱 크기: ${APP_SIZE_MB}MB → DMG 용량: ${DMG_SIZE_MB}MB"

# 임시 읽기-쓰기 이미지 생성
hdiutil create -size "${DMG_SIZE_MB}m" -fs HFS+ -volname "$APP_NAME" "$TMP_DMG"

# 고유한 임시 경로에 마운트 (기존 /Volumes/keeptray 충돌 방지)
mkdir -p "$MOUNT_DIR"
hdiutil attach "$TMP_DMG" -mountpoint "$MOUNT_DIR" -nobrowse
echo "  마운트: $MOUNT_DIR"

# .app 드래그 설치 + 안내 문서
rsync -a --progress "$APP_PATH" "$MOUNT_DIR/"
ln -s /Applications "$MOUNT_DIR/Applications"
if [ -f "docs/install_guide.txt" ]; then
    cp "docs/install_guide.txt" "$MOUNT_DIR/ReadMe.txt"
fi

# 마운트 해제
sync
hdiutil detach "$MOUNT_DIR" -force
rm -rf "$MOUNT_DIR"

# 압축 DMG로 변환
hdiutil convert "$TMP_DMG" -format UDZO -o "dist/${DMG_NAME}"
rm -f "$TMP_DMG"

echo "✓ 완료: dist/${DMG_NAME}"
echo "  크기: $(du -sh "dist/${DMG_NAME}" | cut -f1)"
