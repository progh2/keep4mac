"""py2app 진입점 — src 레이아웃을 path에 추가하고 앱을 시작한다."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from keep4mac.__main__ import main  # noqa: E402

if __name__ == "__main__":
    main()
