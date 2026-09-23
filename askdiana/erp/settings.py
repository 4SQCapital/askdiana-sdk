from __future__ import annotations

import os

_TRUE = frozenset({"1", "true", "yes", "on"})


def env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in _TRUE


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
