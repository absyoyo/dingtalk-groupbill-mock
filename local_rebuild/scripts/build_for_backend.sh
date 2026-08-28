#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVER_URL="${1:-}"

if [[ -z "$SERVER_URL" ]]; then
  printf 'usage: %s <http-or-https-backend-url> [--smoke] [--package <full_package>] [--label <text>] [--overlay-offset-dp <n>] [--uc-auth-bypass]\n' "$0" >&2
  exit 2
fi

shift

SMOKE=0
PACKAGE=""
LABEL=""
OVERLAY_OFFSET_DP=""
UC_AUTH_BYPASS=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --smoke)
      SMOKE=1
      shift
      ;;
    --uc-auth-bypass)
      UC_AUTH_BYPASS=1
      shift
      ;;
    --package)
      PACKAGE="${2:-}"
      if [[ -z "$PACKAGE" ]]; then
        printf 'missing argument for --package\n' >&2
        exit 2
      fi
      shift 2
      ;;
    --label)
      LABEL="${2:-}"
      if [[ -z "$LABEL" ]]; then
        printf 'missing argument for --label\n' >&2
        exit 2
      fi
      shift 2
      ;;
    --overlay-offset-dp)
      OVERLAY_OFFSET_DP="${2:-}"
      if [[ -z "$OVERLAY_OFFSET_DP" ]]; then
        printf 'missing argument for --overlay-offset-dp\n' >&2
        exit 2
      fi
      shift 2
      ;;
    *)
      printf 'unsupported argument: %s\n' "$1" >&2
      exit 2
      ;;
  esac
done

export LOCALTEST_SERVER_URL
LOCALTEST_SERVER_URL="$(PYTHONPATH="$ROOT" python3 -m local_rebuild.patches.backend_config "$SERVER_URL")"

if [[ "$SMOKE" == "1" ]]; then
  export LOCALTEST_HTTP_SMOKE=1
else
  unset LOCALTEST_HTTP_SMOKE || true
fi

if [[ -n "$PACKAGE" ]]; then
  export LOCALTEST_PACKAGE="$PACKAGE"
else
  unset LOCALTEST_PACKAGE || true
fi

if [[ -n "$LABEL" ]]; then
  export LOCALTEST_APP_LABEL="$LABEL"
else
  unset LOCALTEST_APP_LABEL || true
fi

if [[ -n "$OVERLAY_OFFSET_DP" ]]; then
  export LOCALTEST_OVERLAY_OFFSET_DP="$OVERLAY_OFFSET_DP"
else
  unset LOCALTEST_OVERLAY_OFFSET_DP || true
fi

if [[ "$UC_AUTH_BYPASS" == "1" ]]; then
  export LOCALTEST_UC_AUTH_BYPASS=1
else
  unset LOCALTEST_UC_AUTH_BYPASS || true
fi

"$ROOT/local_rebuild/scripts/build_apk.sh"
"$ROOT/local_rebuild/scripts/verify_apk.sh"
printf 'backend-apk-ready %s\n' "$LOCALTEST_SERVER_URL"
