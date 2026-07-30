from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class HttpError(RuntimeError):
    pass


def fetch_text(url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> str:
    request = Request(url, headers=headers or {})
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HttpError(f"Failed to fetch {url}: {exc}") from exc


def fetch_json(url: str, *, headers: dict[str, str] | None = None, timeout: int = 20) -> Any:
    return json.loads(fetch_text(url, headers=headers, timeout=timeout))


def post_json(url: str, payload: dict[str, Any], *, headers: dict[str, str], timeout: int = 30) -> Any:
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="replace")
            return json.loads(body) if body else {}
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HttpError(f"Failed to post to {url}: {exc}") from exc


def post_form(url: str, payload: dict[str, str], *, timeout: int = 20) -> Any:
    data = urlencode(payload).encode("utf-8")
    request = Request(url, data=data, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            body = response.read().decode(charset, errors="replace")
            return json.loads(body) if body else {}
    except (HTTPError, URLError, TimeoutError) as exc:
        raise HttpError(f"Failed to post form to {url}: {exc}") from exc
