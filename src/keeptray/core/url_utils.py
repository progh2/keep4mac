import re

_URL_RE = re.compile(r'https?://[^\s\)\]\}\"\'<>]+')
_BLOCKED_SCHEMES = re.compile(r'^(javascript|data|vbscript|file):', re.IGNORECASE)


def extract_urls(text: str) -> list[str]:
    return [u for u in _URL_RE.findall(text) if not _BLOCKED_SCHEMES.match(u)]


def short_url(url: str, max_len: int = 50) -> str:
    s = url.removeprefix("https://").removeprefix("http://").rstrip("/")
    return s[:max_len] + "…" if len(s) > max_len else s
