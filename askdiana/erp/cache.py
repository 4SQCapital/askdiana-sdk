from __future__ import annotations

import threading
import time
from collections.abc import Callable, Hashable
from typing import Any


class TTLCache:
    def __init__(self, ttl_seconds: int):
        self._ttl = ttl_seconds
        self._items: dict[Hashable, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: Hashable) -> tuple[bool, Any]:
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return False, None
            expires_at, value = entry
            if expires_at <= time.monotonic():
                del self._items[key]
                return False, None
            return True, value
    
    def set(self, key: Hashable, value: Any) -> None:
        with self._lock:
            self._items[key] = (time.monotonic() + self._ttl, value)
    
    def invalidate_where(self, predicate: Callable[[Hashable], bool]) -> None:
        with self._lock:
            for key in [k for k in self._items if predicate(k)]:
                del self._items[key]
