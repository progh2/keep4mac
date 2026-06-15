# -*- mode: python ; coding: utf-8 -*-
# Windows PyInstaller 스펙 — macOS BUNDLE 없음
import os
from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

SRC = str(Path("src").resolve())

_metadata = []
for _pkg in ["gpsoauth", "gkeepapi", "requests", "keyring", "pystray", "PIL",
             "python-docx", "python-hwpx", "certifi", "charset_normalizer"]:
    try:
        _metadata += copy_metadata(_pkg)
    except Exception:
        pass

# 데이터 파일이 필요한 패키지
_extra_data = []
for _pkg in ["docx", "hwpx", "certifi", "playwright"]:
    try:
        _extra_data += collect_data_files(_pkg)
    except Exception:
        pass

# playwright driver 바이너리(node.exe) — collect_data_files는 JS만 반환하므로 별도 추가
_playwright_binaries = []
try:
    import playwright as _pw
    _node_exe = os.path.join(os.path.dirname(_pw.__file__), "driver", "node.exe")
    if os.path.exists(_node_exe):
        _playwright_binaries.append((_node_exe, "playwright/driver"))
except Exception:
    pass

a = Analysis(
    ["main.py"],
    pathex=[SRC],
    binaries=_playwright_binaries,
    datas=[
        (SRC + "/keeptray", "keeptray"),
        ("i18n", "i18n"),
    ] + _metadata + _extra_data,
    hiddenimports=[
        # Qt
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",

        # 인증·키체인
        "keyring",
        "keyring.errors",
        "keyring.backends",
        "keyring.backends.Windows",
        "jaraco.classes",
        "jaraco.functools",
        "jaraco.context",

        # Keep API
        "gkeepapi",
        "gkeepapi.node",
        "gkeepapi.exception",
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

        # Playwright — _driver 는 frozen 경로 계산에 필수
        "playwright.sync_api",
        "playwright.async_api",
        "playwright._impl._api_types",
        "playwright._impl._driver",
        "playwright._impl._connection",
        "playwright._impl._playwright",
        "pyee",
        "greenlet",

        # 트레이 아이콘
        "pystray",
        "pystray._win32",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",

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
        "winreg",
        "zipfile",
        "typing_extensions",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["rthook_qt.py"],
    excludes=["tkinter", "unittest", "rumps", "objc", "AppKit"],
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
    console=False,   # 콘솔 창 없음
    disable_windowed_traceback=False,
    icon="assets/icon.ico",
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
