#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="${MOCK_PID_FILE:-$ROOT/local_rebuild/logs/mock-server.pid}"
STDOUT_LOG="${MOCK_STDOUT_LOG:-$ROOT/local_rebuild/logs/mock-server.stdout.log}"

source "$ROOT/local_rebuild/scripts/server_process.sh"

mkdir -p "$(dirname "$PID_FILE")" "$(dirname "$STDOUT_LOG")"

if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  return 0
fi

if [[ -f "$PID_FILE" ]]; then
  existing_pid="$(<"$PID_FILE")"
  if is_owned_process "$existing_pid"; then
    printf 'mock-server-already-running\n'
    exit 0
  fi
  rm -f "$PID_FILE"
fi

SERVER_HOST="${MOCK_SERVER_HOST:-0.0.0.0}"
HEALTH_HOST="$SERVER_HOST"
[[ "$HEALTH_HOST" == "0.0.0.0" ]] && HEALTH_HOST="127.0.0.1"

PYTHONPATH="$ROOT" nohup python3 -m uvicorn local_rebuild.server.main:app \
  --host "$SERVER_HOST" --port 18722 </dev/null >"$STDOUT_LOG" 2>&1 &
server_pid="$!"
printf '%s\n' "$server_pid" >"$PID_FILE"

for _ in $(seq 1 30); do
  if curl -fsS "http://$HEALTH_HOST:18722/health" >/dev/null 2>&1; then
    printf 'mock-server-ready\n'
    exit 0
  fi
  sleep 0.2
done

printf 'mock-server-start-failed\n' >&2
if is_owned_process "$server_pid"; then
  kill "$server_pid" 2>/dev/null || true
fi
wait "$server_pid" 2>/dev/null || true
rm -f "$PID_FILE"
exit 1
