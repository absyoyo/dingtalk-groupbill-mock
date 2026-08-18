#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MODE="${1:-}"

if [[ -n "$MODE" && "$MODE" != "--smoke" ]]; then
  printf 'usage: %s [--smoke]\n' "$0" >&2
  exit 2
fi

adb get-state >/dev/null
WIFI_STATUS="$(adb shell cmd wifi status 2>/dev/null | tr -d '\r')"
if [[ "${WIFI_STATUS,,}" != *"wifi is connected"* ]]; then
  printf 'phone-wifi-not-connected\n' >&2
  exit 1
fi

PHONE_IP="$(
  adb shell ip -4 -o addr show scope global 2>/dev/null | tr -d '\r' |
    while read -r _ interface _ address _; do
      if [[ "$interface" == wlan* || "$interface" == wifi* ]]; then
        printf '%s\n' "${address%/*}"
        break
      fi
    done
)"
if [[ -z "$PHONE_IP" ]]; then
  printf 'phone-wifi-ipv4-missing\n' >&2
  exit 1
fi

read -ra ROUTE_PARTS <<<"$(ip -4 route get "$PHONE_IP")"
HOST_IP=""
for ((index = 0; index < ${#ROUTE_PARTS[@]} - 1; index++)); do
  if [[ "${ROUTE_PARTS[$index]}" == "src" ]]; then
    HOST_IP="${ROUTE_PARTS[$((index + 1))]}"
    break
  fi
done
if [[ -z "$HOST_IP" ]]; then
  printf 'host-route-to-phone-missing\n' >&2
  exit 1
fi

SERVER_URL="http://$HOST_IP:18722"
if [[ "$MODE" == "--smoke" ]]; then
  "$ROOT/local_rebuild/scripts/build_for_backend.sh" "$SERVER_URL" --smoke
else
  "$ROOT/local_rebuild/scripts/build_for_backend.sh" "$SERVER_URL"
fi
printf 'connected-phone-backend-ready %s\n' "$SERVER_URL"
