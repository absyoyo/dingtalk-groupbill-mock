#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="$ROOT/local_rebuild/logs/mock-server.pid"
FAILURES=0

pass()  { printf 'PASS %s\n' "$1"; }
fail()  { printf 'FAIL %s: %s\n' "$1" "$2"; FAILURES=$((FAILURES + 1)); }

cleanup_pid() { rm -f "$PID_FILE"; }

test_port_available() {
  if ss -ltn | grep -q ':18722'; then
    fail "port 18722 availability" "port-18722-already-in-use"
    return 1
  fi
  pass "port 18722 availability"
}

# ── helper: is_owned_process must be sourceable ──────────────────────────────

source_is_owned() {
  set +e
  source "$ROOT/local_rebuild/scripts/start_server.sh" 2>/dev/null </dev/null
  local rc=$?
  set -e
  if declare -f is_owned_process >/dev/null 2>&1; then
    pass "is_owned_process function is defined"
  else
    fail "is_owned_process function is defined" "function not found after sourcing start_server.sh"
    return 1
  fi
  return "$rc"
}

# ── test 1: is_owned_process rejects non-numeric input ───────────────────────

test_non_numeric_pid() {
  cleanup_pid
  if is_owned_process "not-a-pid"; then
    fail "is_owned_process non-numeric" "accepted non-numeric"
  else
    pass "is_owned_process non-numeric"
  fi
}

# ── test 2: is_owned_process rejects nonexistent PID ────────────────────────

test_nonexistent_pid() {
  cleanup_pid
  if is_owned_process 99999999; then
    fail "is_owned_process nonexistent" "accepted nonexistent PID 99999999"
  else
    pass "is_owned_process nonexistent"
  fi
}

# ── test 3: is_owned_process rejects wrong process ──────────────────────────

test_wrong_process() {
  cleanup_pid
  sleep 10 &
  local spid=$!
  if is_owned_process "$spid"; then
    fail "is_owned_process wrong process" "accepted PID $spid (sleep, not uvicorn)"
  else
    pass "is_owned_process wrong process"
  fi
  kill "$spid" 2>/dev/null || true
  wait "$spid" 2>/dev/null || true
}

# ── test 4: is_owned_process accepts real uvicorn ────────────────────────────

test_valid_uvicorn() {
  cleanup_pid
  PYTHONPATH="$ROOT" nohup python3 -m uvicorn local_rebuild.server.main:app \
    --host 127.0.0.1 --port 18722 </dev/null >/dev/null 2>&1 &
  local upid=$!
  sleep 2
  if is_owned_process "$upid"; then
    pass "is_owned_process valid uvicorn"
  else
    fail "is_owned_process valid uvicorn" "rejected valid uvicorn PID $upid"
  fi
  kill "$upid" 2>/dev/null || true
  wait "$upid" 2>/dev/null || true
}

# ── test 5: stale unowned PID removed on start ───────────────────────────────

test_start_removes_stale_pid() {
  cleanup_pid
  printf '99999999\n' >"$PID_FILE"
  local out
  out="$(bash "$ROOT/local_rebuild/scripts/start_server.sh" 2>&1)"
  local replacement_pid=""
  if [[ -f "$PID_FILE" ]]; then
    replacement_pid="$(<"$PID_FILE")"
  fi
  if [[ "$out" == "mock-server-ready" ]] && is_owned_process "$replacement_pid"; then
    pass "stale PID replaced on start"
  else
    fail "stale PID replaced on start" "got output '$out' and replacement PID '$replacement_pid'"
  fi
  bash "$ROOT/local_rebuild/scripts/stop_server.sh" >/dev/null 2>&1 || true
  cleanup_pid
}

# ── test 6: malformed non-numeric PID rejected by stop ───────────────────────

test_stop_rejects_malformed_pid() {
  cleanup_pid
  echo "garbage" > "$PID_FILE"
  local out
  out="$(bash "$ROOT/local_rebuild/scripts/stop_server.sh" 2>&1)" || true
  if [[ -f "$PID_FILE" ]]; then
    fail "malformed PID rejection" "PID file still exists after stop with malformed PID"
  else
    pass "malformed PID rejection"
  fi
}

# ── test 7: unowned PID not killed by stop ───────────────────────────────────

test_stop_preserves_unowned() {
  cleanup_pid
  sleep 10 &
  local spid=$!
  echo "$spid" > "$PID_FILE"
  local out
  out="$(bash "$ROOT/local_rebuild/scripts/stop_server.sh" 2>&1)" || true
  if kill -0 "$spid" 2>/dev/null; then
    pass "unowned PID not killed by stop"
  else
    fail "unowned PID not killed by stop" "PID $spid was killed"
  fi
  kill "$spid" 2>/dev/null || true
  wait "$spid" 2>/dev/null || true
  cleanup_pid
}

# ── test 8: idempotent start ─────────────────────────────────────────────────

test_idempotent_start() {
  cleanup_pid
  bash "$ROOT/local_rebuild/scripts/start_server.sh" >/dev/null 2>&1
  local out
  out="$(bash "$ROOT/local_rebuild/scripts/start_server.sh" 2>&1)"
  if [[ "$out" == "mock-server-already-running" ]]; then
    pass "idempotent start"
  else
    fail "idempotent start" "got: $out"
  fi
  bash "$ROOT/local_rebuild/scripts/stop_server.sh" >/dev/null 2>&1 || true
}

# ── test 9: full start → smoke → stop cycle ──────────────────────────────────

test_full_cycle() {
  cleanup_pid
  bash "$ROOT/local_rebuild/scripts/start_server.sh" >/dev/null 2>&1
  local smoke_out
  smoke_out="$(PYTHONPATH="$ROOT" python3 "$ROOT/local_rebuild/scripts/host_protocol_smoke.py" 2>&1)"
  if [[ "$smoke_out" == "host-protocol-smoke-ok" ]]; then
    pass "smoke test in cycle"
  else
    fail "smoke test in cycle" "got: $smoke_out"
  fi
  local stop_out
  stop_out="$(bash "$ROOT/local_rebuild/scripts/stop_server.sh" 2>&1)"
  if [[ "$stop_out" == "mock-server-stopped" ]]; then
    pass "stop after cycle"
  else
    fail "stop after cycle" "got: $stop_out"
  fi
}

# ── runner ───────────────────────────────────────────────────────────────────

echo "=== Mock Server Script Tests ==="
echo ""

if ! test_port_available; then
  printf '\n---\nFailures: %s\n' "$FAILURES"
  exit "$FAILURES"
fi
source_is_owned || true
test_non_numeric_pid
test_nonexistent_pid
test_wrong_process
test_valid_uvicorn
test_start_removes_stale_pid
test_stop_rejects_malformed_pid
test_stop_preserves_unowned
test_idempotent_start
test_full_cycle

echo ""
echo "---"
echo "Failures: $FAILURES"
exit "$FAILURES"
