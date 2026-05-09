# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata
import PyQt6 as _PyQt6

SRC = str(Path("src").resolve())
# pip 설치 PyQt6 플러그인 경로 — framework 형식이므로 번들 내 Qt6 libs와 호환
PYQT6_PLUGINS = os.path.join(os.path.dirname(_PyQt6.__file__), "Qt6", "plugins")

# importlib.metadata 를 사용하는 패키지들의 dist-info 포함
_metadata = []
for _pkg in ["gpsoauth", "gkeepapi", "requests", "keyring", "rumps"]:
    try:
        _metadata += copy_metadata(_pkg)
    except Exception:
        pass

a = Analysis(
    ["main.py"],
    pathex=[SRC],
    binaries=[],
    datas=[
        (SRC + "/keep4mac", "keep4mac"),
    ] + _metadata,
    hiddenimports=[
        "objc",
        "AppKit",
        "Foundation",
        "Quartz",
        "CoreFoundation",
        "rumps",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "keyring.backends",
        "keyring.backends.macOS",
        "pkg_resources.py2_warn",
        "playwright.sync_api",
        "playwright.async_api",
        "playwright._impl._api_types",
        "ssl",
        "_ssl",
        "gpsoauth",
        "gpsoauth.google",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["rthook_qt.py"],
    excludes=["tkinter", "unittest"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="keep4mac",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="keep4mac",
)

app = BUNDLE(
    coll,
    name="keep4mac.app",
    bundle_identifier="com.keep4mac.app",
    version="0.1.0",
    info_plist={
        "LSUIElement": True,          # 메뉴바 앱 — Dock 숨김
        "CFBundleName": "keep4mac",
        "CFBundleDisplayName": "keep4mac",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "NSAppleEventsUsageDescription": "Google Keep 로그인에 사용됩니다.",
    },
)
