import re

_URL_RE = re.compile(r'https?://[^\s\)\]\}\"\'<>]+')


def extract_urls(text: str) -> list[str]:
    return _URL_RE.findall(text)


def short_url(url: str, max_len: int = 50) -> str:
    s = url.removeprefix("https://").removeprefix("http://").rstrip("/")
    return s[:max_len] + "…" if len(s) > max_len else s
