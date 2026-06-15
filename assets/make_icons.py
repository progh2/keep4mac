"""
keeptray 아이콘 생성 스크립트.
실행: python assets/make_icons.py
결과: assets/icon.icns, assets/icon.ico, assets/icon_*.png
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS = Path(__file__).parent
ICONSET = ASSETS / "icon.iconset"
ICONSET.mkdir(exist_ok=True)

# Google Keep 브랜드 색상
YELLOW = (251, 188, 4, 255)
WHITE = (255, 255, 255, 255)


def make_app_icon(size: int) -> Image.Image:
    """노란 배경 + 흰 전구 앱 아이콘 (Google Keep 스타일)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 노란 배경 - 둥근 사각형
    pad = max(1, int(size * 0.04))
    radius = int(size * 0.22)
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill=YELLOW,
    )

    # 전구 몸통 (원)
    cx = size / 2
    cy = size * 0.40
    bulb_r = size * 0.20
    draw.ellipse(
        [cx - bulb_r, cy - bulb_r, cx + bulb_r, cy + bulb_r],
        fill=WHITE,
    )

    # 전구 받침 1단
    bw = size * 0.16
    bh1 = size * 0.07
    bx0 = cx - bw / 2
    by0 = cy + bulb_r - size * 0.015
    draw.rounded_rectangle(
        [bx0, by0, bx0 + bw, by0 + bh1],
        radius=max(1, int(size * 0.015)),
        fill=WHITE,
    )

    # 전구 받침 2단 (약간 좁게)
    bw2 = bw * 0.72
    bx2 = cx - bw2 / 2
    by2 = by0 + bh1
    bh2 = size * 0.05
    draw.rounded_rectangle(
        [bx2, by2, bx2 + bw2, by2 + bh2],
        radius=max(1, int(size * 0.015)),
        fill=WHITE,
    )

    return img


def make_tray_icon(size: int) -> Image.Image:
    """트레이용 단색 전구 아이콘 (투명 배경, 흰 전구)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = size / 2
    cy = size * 0.38
    bulb_r = size * 0.26
    draw.ellipse([cx - bulb_r, cy - bulb_r, cx + bulb_r, cy + bulb_r], fill=WHITE)

    bw = size * 0.20
    bh1 = size * 0.09
    bx0 = cx - bw / 2
    by0 = cy + bulb_r - size * 0.02
    draw.rounded_rectangle([bx0, by0, bx0 + bw, by0 + bh1],
                           radius=max(1, int(size * 0.02)), fill=WHITE)

    bw2 = bw * 0.72
    bx2 = cx - bw2 / 2
    by2 = by0 + bh1
    draw.rounded_rectangle([bx2, by2, bx2 + bw2, by2 + size * 0.06],
                           radius=max(1, int(size * 0.02)), fill=WHITE)
    return img


def build_icns():
    """macOS iconset → icns 변환."""
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    for s in sizes:
        icon = make_app_icon(s)
        icon.save(ICONSET / f"icon_{s}x{s}.png")
        # Retina (@2x) — 절반 크기 슬롯에 2배 해상도
        if s <= 512:
            icon.save(ICONSET / f"icon_{s}x{s}@2x.png")

    result = subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET), "-o", str(ASSETS / "icon.icns")],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"iconutil 오류: {result.stderr}", file=sys.stderr)
        return False
    print(f"✓ icon.icns 생성 완료")
    return True


def build_ico():
    """Windows 멀티 해상도 ICO 생성."""
    ico_path = ASSETS / "icon.ico"
    # PIL ICO: 가장 큰 이미지에 sizes= 파라미터로 자동 리사이즈
    master = make_app_icon(256).convert("RGBA")
    master.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"✓ icon.ico 생성 완료 ({ico_path.stat().st_size // 1024}KB)")


def build_tray_png():
    """Windows 트레이용 PNG (64×64, 흰 전구)."""
    tray = make_tray_icon(64)
    tray.save(ASSETS / "tray_icon.png")
    print(f"✓ tray_icon.png 생성 완료")


if __name__ == "__main__":
    build_icns()
    build_ico()
    build_tray_png()
    print("아이콘 생성 완료.")
