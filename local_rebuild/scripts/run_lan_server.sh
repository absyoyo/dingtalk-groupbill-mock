#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
METADATA="$ROOT/local_rebuild/dist/dingtalk-localtest.backend-url"
EVENT_LOG="$ROOT/local_rebuild/logs/mock-events.jsonl"
START_SCRIPT="$ROOT/local_rebuild/scripts/start_server.sh"
STOP_SCRIPT="$ROOT/local_rebuild/scripts/stop_server.sh"

if [[ ! -s "$METADATA" ]]; then
  printf 'default-backend-metadata-missing\n' >&2
  printf 'build first: local_rebuild/scripts/build_for_backend.sh http://<lan-ip>:18722\n' >&2
  exit 1
fi

SERVER_URL="$(<"$METADATA")"
NORMALIZED_URL="$(PYTHONPATH="$ROOT" python3 -m local_rebuild.patches.backend_config "$SERVER_URL")"
if [[ "$SERVER_URL" != "$NORMALIZED_URL" || "$SERVER_URL" != http://*:18722 ]]; then
  printf 'lan-console-requires-http-port-18722 %s\n' "$SERVER_URL" >&2
  exit 1
fi
WS_URL="ws://${SERVER_URL#http://}/ws"

cleanup() {
  trap - EXIT INT TERM
  "$STOP_SCRIPT" >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

"$START_SCRIPT"
mkdir -p "$(dirname "$EVENT_LOG")"
touch "$EVENT_LOG"
printf 'lan-server-http %s\n' "$SERVER_URL"
printf 'lan-server-websocket %s\n' "$WS_URL"
printf 'lan-server-events %s\n' "$EVENT_LOG"
printf 'press-ctrl-c-to-stop\n'
tail -n 0 -F "$EVENT_LOG"
