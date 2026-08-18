#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APK="$ROOT/local_rebuild/dist/dingtalk-localtest.apk"
BACKEND_METADATA="$ROOT/local_rebuild/dist/dingtalk-localtest.backend-url"
LOG="$ROOT/local_rebuild/logs/device-launch.log"
OFFICIAL="com.alibaba.android.rimet"
LOCALTEST="com.alibaba.android.rimet.localtest"

test -s "$BACKEND_METADATA"
adb get-state >/dev/null
adb reverse --remove tcp:18722 >/dev/null 2>&1 || true
if adb reverse --list 2>/dev/null | grep -Fq 'tcp:18722 tcp:18722'; then
  printf 'adb-reverse-removal-failed\n' >&2
  exit 1
fi
adb install -r "$APK" >"$ROOT/local_rebuild/logs/device-install.log" 2>&1
adb shell pm path "$OFFICIAL" >/dev/null
adb shell pm path "$LOCALTEST" >/dev/null

adb logcat -c
adb shell am start -W -n \
  "$LOCALTEST/com.alibaba.android.rimet.biz.LaunchHomeActivity" \
  >"$ROOT/local_rebuild/logs/device-am-start.log" 2>&1
sleep 8
adb logcat -d -v time >"$LOG"

if grep -Fq "Process: $LOCALTEST," "$LOG"; then
  printf 'localtest-startup-crash\n' >&2
  exit 1
fi
printf 'device-setup-ok\n'
