#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVER_URL="${1:-}"
MODE="${2:-}"

if [[ -z "$SERVER_URL" ]]; then
  printf 'usage: %s <http-or-https-backend-url> [--smoke]\n' "$0" >&2
  exit 2
fi
if [[ -n "$MODE" && "$MODE" != "--smoke" ]]; then
  printf 'unsupported-build-mode %s\n' "$MODE" >&2
  exit 2
fi

export LOCALTEST_SERVER_URL
LOCALTEST_SERVER_URL="$(PYTHONPATH="$ROOT" python3 -m local_rebuild.patches.backend_config "$SERVER_URL")"
if [[ "$MODE" == "--smoke" ]]; then
  export LOCALTEST_HTTP_SMOKE=1
else
  unset LOCALTEST_HTTP_SMOKE || true
fi

"$ROOT/local_rebuild/scripts/build_apk.sh"
"$ROOT/local_rebuild/scripts/verify_apk.sh"
printf 'backend-apk-ready %s\n' "$LOCALTEST_SERVER_URL"
