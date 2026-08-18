#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APKTOOL="$ROOT/local_rebuild/tools/apktool_3.0.3.jar"
SMALI_CP="$ROOT/local_rebuild/tools/jadx-1.4.7/lib/*"
VERIFY_MANIFEST="$ROOT/local_rebuild/source/verify-manifest"
DEX_CHECK="$ROOT/local_rebuild/source/verify-dex"
VERIFY_SMALI="$ROOT/local_rebuild/source/verify-smali"
LOGS="$ROOT/local_rebuild/logs"
: "${LOCALTEST_SERVER_URL:?set LOCALTEST_SERVER_URL to the backend base URL}"
SERVER_URL="$(PYTHONPATH="$ROOT" python3 -m local_rebuild.patches.backend_config "$LOCALTEST_SERVER_URL")"

if [[ "${LOCALTEST_HTTP_SMOKE:-0}" == "1" ]]; then
  APK="$ROOT/local_rebuild/dist/dingtalk-localtest-smoke.apk"
  METADATA="$ROOT/local_rebuild/dist/dingtalk-localtest-smoke.backend-url"
else
  APK="$ROOT/local_rebuild/dist/dingtalk-localtest.apk"
  METADATA="$ROOT/local_rebuild/dist/dingtalk-localtest.backend-url"
fi

cmp -s "$ROOT/working.apk" "$ROOT/local_rebuild/input/working.apk"
test -s "$APK"
test -s "$METADATA"
if [[ "$(<"$METADATA")" != "$SERVER_URL" ]]; then
  printf 'backend-metadata-mismatch\n' >&2
  exit 1
fi
unzip -Z1 "$APK" >"$LOGS/verify-00-entries.txt"
grep -Fxq 'AndroidManifest.xml' "$LOGS/verify-00-entries.txt"
zipalign -c -p 4 "$APK" >"$LOGS/verify-01-zipalign.log" 2>&1
apksigner verify --verbose "$APK" >"$LOGS/verify-02-signature.log" 2>&1

rm -rf "$VERIFY_MANIFEST" "$DEX_CHECK" "$VERIFY_SMALI"
java -jar "$APKTOOL" d -f --only-manifest -s "$APK" -o "$VERIFY_MANIFEST" \
  >"$LOGS/verify-03-manifest-decode.log" 2>&1
PYTHONPATH="$ROOT" python3 "$ROOT/local_rebuild/patches/verify_manifest.py" \
  "$VERIFY_MANIFEST/AndroidManifest.xml" >"$LOGS/verify-04-manifest.log"

mkdir -p "$DEX_CHECK"
unzip -j -o "$APK" classes33.dex classes36.dex classes37.dex classes38.dex -d "$DEX_CHECK" \
  >"$LOGS/verify-05-dex-extract.log"

for dex in classes33 classes36 classes37 classes38; do
  mkdir -p "$VERIFY_SMALI/$dex"
  java -cp "$SMALI_CP" org.jf.baksmali.Main d "$DEX_CHECK/$dex.dex" \
    -o "$VERIFY_SMALI/$dex" >>"$LOGS/verify-06-baksmali.log" 2>&1
done
SMALI_VERIFY_ARGS=(--verify)
if [[ "${LOCALTEST_HTTP_SMOKE:-0}" == "1" ]]; then
  SMALI_VERIFY_ARGS+=(--http-smoke)
fi
PYTHONPATH="$ROOT" python3 "$ROOT/local_rebuild/patches/patch_smali.py" \
  --server-url "$SERVER_URL" "${SMALI_VERIFY_ARGS[@]}" "$VERIFY_SMALI" \
  >"$LOGS/verify-07-smali.log"

printf 'apk-static-verify-ok\n'
