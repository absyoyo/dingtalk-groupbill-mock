#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PID_FILE="${MOCK_PID_FILE:-$ROOT/local_rebuild/logs/mock-server.pid}"

source "$ROOT/local_rebuild/scripts/server_process.sh"

if [[ ! -f "$PID_FILE" ]]; then
  printf 'mock-server-not-running\n'
  exit 0
fi

PID="$(<"$PID_FILE")"
if ! is_owned_process "$PID"; then
  rm -f "$PID_FILE"
  printf 'mock-server-stale-pid-removed\n'
  exit 0
fi

kill "$PID"
for _ in $(seq 1 50); do
  if ! is_owned_process "$PID"; then
    rm -f "$PID_FILE"
    printf 'mock-server-stopped\n'
    exit 0
  fi
  sleep 0.1
done

printf 'mock-server-stop-failed\n' >&2
exit 1
