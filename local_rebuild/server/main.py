from pathlib import Path

from local_rebuild.server.app import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[2]
app = create_app(PROJECT_ROOT / "local_rebuild" / "logs" / "mock-events.jsonl")
