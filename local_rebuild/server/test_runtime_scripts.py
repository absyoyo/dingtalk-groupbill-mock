import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT_ROOT / "local_rebuild" / "scripts"
LAN_CONSOLE = SCRIPTS / "run_lan_server.sh"
PROCESS_HELPERS = SCRIPTS / "server_process.sh"


def test_sourcing_start_script_defines_helpers_without_starting_server(tmp_path):
    pid_file = tmp_path / "mock-server.pid"
    environment = os.environ.copy()
    environment["MOCK_PID_FILE"] = str(pid_file)
    environment["MOCK_STDOUT_LOG"] = str(tmp_path / "mock-server.log")

    try:
        result = subprocess.run(
            [
                "bash",
                "-c",
                'source "$1"; declare -F is_owned_process >/dev/null',
                "bash",
                str(SCRIPTS / "start_server.sh"),
            ],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )

        assert result.stdout == ""
        assert not pid_file.exists()
    finally:
        subprocess.run(
            [str(SCRIPTS / "stop_server.sh")],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            timeout=10,
            check=False,
        )


def test_stop_script_never_kills_an_unowned_stale_pid(tmp_path):
    pid_file = tmp_path / "mock-server.pid"
    unrelated = subprocess.Popen(["sleep", "30"])
    try:
        pid_file.write_text(f"{unrelated.pid}\n", encoding="utf-8")
        environment = os.environ.copy()
        environment["MOCK_PID_FILE"] = str(pid_file)

        result = subprocess.run(
            [str(SCRIPTS / "stop_server.sh")],
            cwd=PROJECT_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )

        assert unrelated.poll() is None
        assert result.stdout.strip() == "mock-server-stale-pid-removed"
        assert not pid_file.exists()
    finally:
        if unrelated.poll() is None:
            unrelated.terminate()
            unrelated.wait(timeout=5)
        pid_file.unlink(missing_ok=True)


def test_server_scripts_verify_pid_ownership_before_signalling():
    helper_source = PROCESS_HELPERS.read_text(encoding="utf-8")
    assert "is_owned_process" in helper_source
    assert "/proc/$pid/cmdline" in helper_source
    assert "local_rebuild.server.main:app" in helper_source
    assert "--port 18722" in helper_source

    for name in ("start_server.sh", "stop_server.sh"):
        script = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "server_process.sh" in script
        assert "is_owned_process" in script
        assert "MOCK_PID_FILE" in script
        assert "is_owned_process()" not in script


def test_host_smoke_has_bounded_http_and_websocket_io():
    source = (SCRIPTS / "host_protocol_smoke.py").read_text(encoding="utf-8")
    assert "timeout=httpx.Timeout(10.0)" in source
    assert "open_timeout=10" in source
    assert "close_timeout=5" in source
    assert source.count("asyncio.wait_for(") >= 2


def test_lan_console_starts_owned_server_and_streams_connection_events():
    source = LAN_CONSOLE.read_text(encoding="utf-8")
    assert "dingtalk-localtest.backend-url" in source
    assert "start_server.sh" in source
    assert "stop_server.sh" in source
    assert "mock-events.jsonl" in source
    assert "tail -n 0 -F" in source
    assert "trap" in source


def test_shell_lifecycle_test_fails_clearly_when_server_port_is_busy():
    source = (SCRIPTS / "test_server_scripts.sh").read_text(encoding="utf-8")
    assert "port 18722 availability" in source
    assert "port-18722-already-in-use" in source
