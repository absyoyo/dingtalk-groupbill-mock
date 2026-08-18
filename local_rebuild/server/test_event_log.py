import json
import pathlib
import tempfile
from concurrent.futures import ThreadPoolExecutor

from local_rebuild.server.event_log import EventLog


def test_append_one_event_writes_complete_jsonl_record():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = pathlib.Path(tmpdir) / "events.jsonl"
        log = EventLog(log_path)
        log.append(
            connection_id="conn-1",
            direction="in",
            transport="ws",
            event_type="message",
            payload={"text": "hello"},
        )

        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["timestamp"] > 0
        assert record["connection_id"] == "conn-1"
        assert record["direction"] == "in"
        assert record["transport"] == "ws"
        assert record["type"] == "message"
        assert record["payload"] == {"text": "hello"}


def test_append_40_events_concurrently_creates_40_valid_json_lines():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = pathlib.Path(tmpdir) / "events.jsonl"
        log = EventLog(log_path)

        def _write(i: int):
            log.append(
                connection_id=f"conn-{i}",
                direction="out",
                transport="http",
                event_type="response",
                payload={"idx": i},
            )

        with ThreadPoolExecutor(max_workers=8) as pool:
            pool.map(_write, range(40))

        lines = log_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 40, f"Expected 40 lines, got {len(lines)}"

        expected_pairs = {(f"conn-{i}", i) for i in range(40)}
        actual_pairs = set()

        for line in lines:
            record = json.loads(line)
            assert record["timestamp"] > 0
            assert record["direction"] == "out"
            assert record["transport"] == "http"
            assert record["type"] == "response"
            actual_pairs.add((record["connection_id"], record["payload"]["idx"]))

        assert actual_pairs == expected_pairs
