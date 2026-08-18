"""In-process event fan-out with a bounded recent-event buffer."""

from __future__ import annotations

import asyncio
from collections import deque
from typing import Any


class EventHub:
    """Broadcast every appended event to admin subscribers and keep a
    bounded tail of recent events for late joiners."""

    def __init__(self, capacity: int = 1000) -> None:
        self._buffer: deque[dict[str, Any]] = deque(maxlen=capacity)
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def publish(self, event: dict[str, Any]) -> None:
        self._buffer.append(event)
        for queue in list(self._subscribers):
            queue.put_nowait(event)

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=500)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    def subscriber_count(self) -> int:
        return len(self._subscribers)

    def recent(self) -> list[dict[str, Any]]:
        return list(self._buffer)