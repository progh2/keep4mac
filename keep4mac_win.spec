# -*- mode: python ; coding: utf-8 -*-
# Windows PyInstaller 스펙 — macOS BUNDLE 없음
from pathlib import Path
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

SRC = str(Path("src").resolve())

_metadata = []
for _pkg in ["gpsoauth", "gkeepapi", "requests", "keyring", "pystray", "PIL",
             "python-docx", "python-hwpx"]:
    try:
        _metadata += copy_metadata(_pkg)
    except Exception:
        pass

# python-docx / python-hwpx 템플릿·스켈레톤 파일 포함
_extra_data = []
for _pkg in ["docx", "hwpx"]:
    try:
        _extra_data += collect_data_files(_pkg)
    except Exception:
        pass

a = Analysis(
    ["main.py"],
    pathex=[SRC],
    binaries=[],
    datas=[
        (SRC + "/keep4mac", "keep4mac"),
        ("i18n", "i18n"),
    ] + _metadata + _extra_data,
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "keyring.backends",
        "keyring.backends.Windows",
        "pkg_resources.py2_warn",
        "playwright.sync_api",
        "playwright.async_api",
        "playwright._impl._api_types",
        "ssl",
        "_ssl",
        "gpsoauth",
        "gpsoauth.google",
        "pystray",
        "pystray._win32",
        "PIL",
        "PIL.Image",
        "PIL.ImageDraw",
        "winreg",
        "docx",
        "docx.oxml",
        "docx.oxml.ns",
        "docx.shared",
        "docx.enum.text",
        "hwpx",
        "lxml",
        "lxml.etree",
        "lxml._elementpath",
        "zipfile",
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
    name="keep4mac",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,   # 콘솔 창 없음
    disable_windowed_traceback=False,
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
