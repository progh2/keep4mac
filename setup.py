"""py2app 빌드 설정."""
from setuptools import setup

APP = ["main.py"]

OPTIONS = {
    "argv_emulation": False,      # macOS 10.15+ 에서 필수
    "semi_standalone": False,     # 완전 독립 번들
    "packages": [
        "keep4mac",
        "PyQt6",
        "rumps",
        "gkeepapi",
        "keyring",
        "requests",
        "playwright",
        "objc",
        "certifi",
        "charset_normalizer",
        "urllib3",
    ],
    "includes": [
        "AppKit",
        "Foundation",
        "Quartz",
    ],
    "excludes": [
        "tkinter",
        "unittest",
        "email",
        "html",
        "http",
        "xmlrpc",
    ],
    "plist": {
        "LSUIElement": True,                          # 메뉴바 앱 — Dock에 표시 안 함
        "CFBundleName": "keep4mac",
        "CFBundleDisplayName": "keep4mac",
        "CFBundleIdentifier": "com.keep4mac.app",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        "NSHighResolutionCapable": True,
        "NSAppleEventsUsageDescription": "Google Keep 로그인에 사용됩니다.",
    },
}

setup(
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
