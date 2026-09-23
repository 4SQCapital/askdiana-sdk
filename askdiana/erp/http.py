from __future__ import annotations

import logging
import random
import time
from http.cookiejar import DefaultCookiePolicy

import requests

from . import constants as C

logger = logging.getLogger(__name__)
_session = requests.Session()
_session.cookies.set_policy(DefaultCookiePolicy(allowed_domains=[]))


def request(
    method: str,
    url: str,
    *,
    timeout: float = C.HTTP_TIMEOUT_SECONDS,
    retry: bool = True,
    **kwargs,
) -> requests.Response:
    attempts = C.RETRY_MAX_ATTEMPTS if retry else 1
    for attempt in range(1, attempts + 1):
        try:
            response = _session.request(method, url, timeout=timeout, **kwargs)
        except (requests.ConnectionError, requests.Timeout):
            if response.status_code in C.RETRY_STATUSES and attempt < attempts:
                logger.info("HTTP %s from %s, retry %d/%d", response.status_code, url, attempt, attempts - 1)
                _backoff(attempt, retry_after=response.headers.get("Retry-After"))
                continue
        return response
    raise RuntimeError("unreachable")


def _backoff(attempt: int, *, retry_after: str | None) -> None:
    if retry_after and retry_after.isdigit():
        delay = float(retry_after)
    else:
        delay = C.RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)) + random.uniform(0, C.RETRY_BASE_DELAY_SECONDS)
    time.sleep(min(delay, C.RETRY_MAX_DELAY_SECONDS))


def json_or_empty(response: requests.Response) -> dict:
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}
