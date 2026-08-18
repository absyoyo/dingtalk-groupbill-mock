import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RUN_SCRIPT = PROJECT_ROOT / "run.sh"


def test_run_sh_is_executable_with_four_modes():
    source = RUN_SCRIPT.read_text(encoding="utf-8")
    assert os.access(RUN_SCRIPT, os.X_OK)
    for mode in ("dev", "build", "stop", "console"):
        assert mode in source
    assert "start_server.sh" in source or "uvicorn local_rebuild.server.main:app" in source
    assert "stop_server.sh" in source
    assert "npm run build" in source
    assert "npm run dev" in source or "vite" in source
    assert "5173" in source
    assert "18722" in source
    assert "0.0.0.0" in source


def test_run_sh_stop_exits_cleanly():
    result = subprocess.run(
        [str(RUN_SCRIPT), "stop"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    assert "mock-server-stopped" in result.stdout or "mock-server-not-running" in result.stdout