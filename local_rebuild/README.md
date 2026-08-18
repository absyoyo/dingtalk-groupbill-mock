# Local Rebuild Usage

## Single Menu Entry

Run from the analysis project root:

```bash
./start.sh
```

The menu separately controls the mock server and APK. Starting or stopping the
server does not require ADB. Installing or launching the APK does not require the
local server because the APK may use either a LAN address or a remote domain.
ADB is used only for optional connected-phone address detection, APK installation,
launch, stop, and log collection; application traffic never uses ADB reverse.

## Artifacts

- `dist/dingtalk-localtest.apk`: normal local test build; no automatic synthetic HTTP request.
- `dist/dingtalk-localtest.backend-url`: backend embedded in the normal APK.
- `dist/dingtalk-localtest-smoke.apk`: validated smoke build; sends one synthetic `upload_order` after module loading.
- `dist/dingtalk-localtest-smoke.backend-url`: backend embedded in the Smoke APK.

Run all commands below from the analysis project root.

## Install Server Dependencies

```bash
python3 -m pip install -r local_rebuild/server/requirements.txt
```

## Build For Any Backend

```bash
local_rebuild/scripts/build_for_backend.sh http://<computer-lan-ip>:18722
local_rebuild/scripts/build_for_backend.sh https://api.example.com
```

Simplest LAN build for the currently connected phone:

```bash
local_rebuild/scripts/build_for_connected_phone.sh
```

This reads the phone Wi-Fi IPv4 address over ADB, asks the host routing table
which local source address reaches that phone, then builds and verifies the APK
for `http://<selected-host-address>:18722`. Use `--smoke` for the Smoke APK.
Run it again whenever the computer changes network interfaces or receives a new
LAN address.

The backend must be an `http` or `https` base URL without credentials, a path,
query parameters, a fragment, or a trailing slash. HTTP requests use that URL
directly. WebSocket requests automatically use `ws` or `wss` plus `/ws`.

One-time HTTP Smoke build:

```bash
local_rebuild/scripts/build_for_backend.sh http://<computer-lan-ip>:18722 --smoke
```

## Start LAN Service And Watch Online/Offline

The computer and phone must be on the same trusted Wi-Fi network. Build the
normal APK for the computer LAN address first, then run:

```bash
local_rebuild/scripts/run_lan_server.sh
```

The console prints the configured HTTP/WebSocket URLs and streams
`local_rebuild/logs/mock-events.jsonl`. New `connected`, `disconnected`,
`register`, `ping`, HTTP report, and downlink records appear while the phone is
used. Press `Ctrl+C` to stop the owned mock server.

For background-only operation:

```bash
local_rebuild/scripts/start_server.sh
curl -fsS http://127.0.0.1:18722/health
```

Host-side HTTP/WebSocket protocol smoke:

```bash
python3 local_rebuild/scripts/host_protocol_smoke.py
```

## Install And Launch

```bash
local_rebuild/scripts/device_setup.sh
```

This removes any stale `adb reverse tcp:18722` rule, installs only
`com.alibaba.android.rimet.localtest`, verifies the official package still
exists, launches the test activity, and records logcat. The APK therefore uses
Wi-Fi LAN or the configured remote domain, never USB port forwarding.

## Send A WebSocket Test Message

```bash
curl -fsS -X POST http://127.0.0.1:18722/debug/ws/send \
  -H 'Content-Type: application/json' \
  -d '{"type":"bill.done","data":{"groupBillId":"local-debug-bill","payId":"local-debug-pay"}}'
```

## Cleanup

```bash
local_rebuild/scripts/device_cleanup.sh
local_rebuild/scripts/stop_server.sh
```

Cleanup force-stops only the localtest package and removes the ADB reverse rule. It does not uninstall or stop the official DingTalk package.
