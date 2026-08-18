#!/usr/bin/env bash
set -euo pipefail

adb shell am force-stop com.alibaba.android.rimet.localtest || true
adb reverse --remove tcp:18722 || true
printf 'device-cleanup-ok\n'
