"""Thread-safe append-only JSONL event logger."""

import json
import pathlib
import threading
import time


class EventLog:
    """A thread-safe, append-only JSON Lines event log.

    Each call to :meth:`append` writes one complete JSON line (terminated
    by a newline) to the backing file.  The file is opened in append mode
    so prior records are never truncated.
    """

    def __init__(self, filepath: str | pathlib.Path) -> None:
        """Open (or create) the event log at *filepath*.

        Creates parent directories automatically.  A :class:`threading.Lock`
        serialises concurrent writes.
        """
        self._filepath = pathlib.Path(filepath)
        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def append(
        self,
        connection_id: str,
        direction: str,
        transport: str,
        event_type: str,
        payload: object,
    ) -> None:
        """Atomically write a single JSON-line record to the log.

        Builds the record dict from the individual fields and delegates to
        :meth:`append_record`.

        Parameters
        ----------
        connection_id:
            Opaque identifier for the connection.
        direction:
            ``"in"`` or ``"out"``.
        transport:
            Transport used (e.g. ``"ws"``, ``"http"``).
        event_type:
            Application-level event type.
        payload:
            Serializable payload written with ``default=str``.
        """
        record = {
            "timestamp": time.time(),
            "connection_id": connection_id,
            "direction": direction,
            "transport": transport,
            "type": event_type,
            "payload": payload,
        }
        self.append_record(record)

    def append_record(self, event: dict) -> None:
        """Atomically append a pre-built event dict as one JSON line.

        Parameters
        ----------
        event:
            Serializable event dict; written with ``default=str`` and
            ``ensure_ascii=False``, terminated by a newline.
        """
        line = json.dumps(event, ensure_ascii=False, default=str) + "\n"
        with self._lock:
            with open(self._filepath, "a", encoding="utf-8") as fh:
                fh.write(line)
