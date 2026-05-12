# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata, collect_data_files
import PyQt6 as _PyQt6

SRC = str(Path("src").resolve())
# pip 설치 PyQt6 플러그인 경로 — framework 형식이므로 번들 내 Qt6 libs와 호환
PYQT6_PLUGINS = os.path.join(os.path.dirname(_PyQt6.__file__), "Qt6", "plugins")

# importlib.metadata 를 사용하는 패키지들의 dist-info 포함
_metadata = []
for _pkg in ["gpsoauth", "gkeepapi", "requests", "keyring", "rumps", "PIL",
             "python-docx", "python-hwpx", "certifi", "charset_normalizer"]:
    try:
        _metadata += copy_metadata(_pkg)
    except Exception:
        pass

# 데이터 파일이 필요한 패키지 (docx 템플릿, hwpx 스켈레톤, certifi SSL 인증서)
_extra_data = []
for _pkg in ["docx", "hwpx", "certifi"]:
    try:
        _extra_data += collect_data_files(_pkg)
    except Exception:
        pass

a = Analysis(
    ["main.py"],
    pathex=[SRC],
    binaries=[],
    datas=[
        (SRC + "/keeptray", "keeptray"),
        ("i18n", "i18n"),
    ] + _metadata + _extra_data,
    hiddenimports=[
        # macOS 네이티브
        "objc",
        "AppKit",
        "Foundation",
        "Quartz",
        "CoreFoundation",
        "rumps",

        # Qt
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",

        # 인증·키체인
        "keyring",
        "keyring.errors",
        "keyring.backends",
        "keyring.backends.macOS",
        "jaraco.classes",
        "jaraco.functools",
        "jaraco.context",

        # Keep API
        "gkeepapi",
        "gkeepapi.node",
        "gpsoauth",
        "gpsoauth.google",
        "future",
        "future.moves",

        # 네트워크·SSL
        "requests",
        "urllib3",
        "urllib3.util",
        "urllib3.util.retry",
        "certifi",
        "charset_normalizer",
        "idna",

        # Playwright
        "playwright.sync_api",
        "playwright.async_api",
        "playwright._impl._api_types",
        "pyee",
        "greenlet",

        # 문서 저장
        "docx",
        "docx.oxml",
        "docx.oxml.ns",
        "docx.shared",
        "docx.enum.text",
        "hwpx",
        "lxml",
        "lxml.etree",
        "lxml._elementpath",

        # 기타 런타임
        "pkg_resources.py2_warn",
        "ssl",
        "_ssl",
        "zipfile",
        "typing_extensions",
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
    name="keeptray",
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
    name="keeptray",
)

app = BUNDLE(
    coll,
    name="keeptray.app",
    bundle_identifier="com.keeptray.app",
    version="0.1.78",
    info_plist={
        "LSUIElement": True,          # 메뉴바 앱 — Dock 숨김
        "CFBundleName": "keeptray",
        "CFBundleDisplayName": "keeptray",
        "CFBundleShortVersionString": "0.1.78",
        "NSHighResolutionCapable": True,
        "NSAppleEventsUsageDescription": "Google Keep 로그인에 사용됩니다.",
    },
)
