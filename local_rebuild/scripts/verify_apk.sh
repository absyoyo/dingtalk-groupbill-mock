#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APKTOOL="$ROOT/local_rebuild/tools/apktool_3.0.3.jar"
SMALI_CP="$ROOT/local_rebuild/tools/jadx-1.4.7/lib/*"
VERIFY_MANIFEST="$ROOT/local_rebuild/source/verify-manifest"
DEX_CHECK="$ROOT/local_rebuild/source/verify-dex"
VERIFY_SMALI="$ROOT/local_rebuild/source/verify-smali"
LOGS="$ROOT/local_rebuild/logs"
PACKAGE="${LOCALTEST_PACKAGE:-com.alibaba.android.rimet.localtest}"
OLD_PKG_PREFIX="com.alibaba.android.rimet."

if [[ "$PACKAGE" != "$OLD_PKG_PREFIX"* || "$PACKAGE" == "$OLD_PKG_PREFIX" ]]; then
  printf 'invalid-package-prefix: %s (must start with %s<suffix>)\n' "$PACKAGE" "$OLD_PKG_PREFIX" >&2
  exit 1
fi
VARIANT="${PACKAGE#$OLD_PKG_PREFIX}"

: "${LOCALTEST_SERVER_URL:?set LOCALTEST_SERVER_URL to the backend base URL}"
SERVER_URL="$(PYTHONPATH="$ROOT" python3 -m local_rebuild.patches.backend_config "$LOCALTEST_SERVER_URL")"

if [[ "${LOCALTEST_HTTP_SMOKE:-0}" == "1" ]]; then
  APK="$ROOT/local_rebuild/dist/dingtalk-$VARIANT-smoke.apk"
  METADATA="$ROOT/local_rebuild/dist/dingtalk-$VARIANT-smoke.backend-url"
else
  APK="$ROOT/local_rebuild/dist/dingtalk-$VARIANT.apk"
  METADATA="$ROOT/local_rebuild/dist/dingtalk-$VARIANT.backend-url"
fi
# default artifact comment: dingtalk-localtest-smoke.apk

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
  --new-package "$PACKAGE" \
  "$VERIFY_MANIFEST/AndroidManifest.xml" >"$LOGS/verify-04-manifest.log"

mkdir -p "$DEX_CHECK"
VERIFY_DEXS="classes33 classes36 classes37 classes38"
if [[ "${LOCALTEST_UC_AUTH_BYPASS:-0}" == "1" ]]; then
  VERIFY_DEXS="classes25 $VERIFY_DEXS"
fi
DEX_EXTRACT_ARGS=()
for dex in $VERIFY_DEXS; do
  DEX_EXTRACT_ARGS+=("$dex.dex")
done
unzip -j -o "$APK" "${DEX_EXTRACT_ARGS[@]}" -d "$DEX_CHECK" \
  >"$LOGS/verify-05-dex-extract.log"

for dex in $VERIFY_DEXS; do
  mkdir -p "$VERIFY_SMALI/$dex"
  java -cp "$SMALI_CP" org.jf.baksmali.Main d "$DEX_CHECK/$dex.dex" \
    -o "$VERIFY_SMALI/$dex" >>"$LOGS/verify-06-baksmali.log" 2>&1
done
SMALI_VERIFY_ARGS=(--verify --new-package "$PACKAGE")
if [[ "${LOCALTEST_HTTP_SMOKE:-0}" == "1" ]]; then
  SMALI_VERIFY_ARGS+=(--http-smoke)
fi
if [[ "${LOCALTEST_OVERLAY_OFFSET_DP:-0}" != "0" ]]; then
  SMALI_VERIFY_ARGS+=(--overlay-offset-dp "${LOCALTEST_OVERLAY_OFFSET_DP}")
fi
if [[ "${LOCALTEST_UC_AUTH_BYPASS:-0}" == "1" ]]; then
  SMALI_VERIFY_ARGS+=(--uc-auth-bypass)
fi
PYTHONPATH="$ROOT" python3 "$ROOT/local_rebuild/patches/patch_smali.py" \
  --server-url "$SERVER_URL" "${SMALI_VERIFY_ARGS[@]}" "$VERIFY_SMALI" \
  >"$LOGS/verify-07-smali.log"

printf 'apk-static-verify-ok\n'
