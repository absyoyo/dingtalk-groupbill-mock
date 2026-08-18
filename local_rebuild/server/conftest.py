import json

import pytest
from fastapi.testclient import TestClient

from local_rebuild.server.app import create_app


@pytest.fixture
def event_path(tmp_path):
    return tmp_path / "events.jsonl"


@pytest.fixture
def client(event_path):
    with TestClient(create_app(event_path)) as test_client:
        yield test_client


@pytest.fixture
def events(event_path):
    def load():
        if not event_path.exists():
            return []
        return [json.loads(line) for line in event_path.read_text(encoding="utf-8").splitlines()]

    return load
