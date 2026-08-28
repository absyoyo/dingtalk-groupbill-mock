#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APKTOOL="$ROOT/local_rebuild/tools/apktool_3.0.3.jar"
SMALI_CP="$ROOT/local_rebuild/tools/jadx-1.4.7/lib/*"
INPUT="$ROOT/local_rebuild/input/working.apk"
SOURCE="$ROOT/local_rebuild/source"
DECODED="$SOURCE/decoded"
DEX_INPUT="$SOURCE/dex-input"
SMALI_ROOT="$SOURCE/smali"
DEX_PATCHED="$SOURCE/dex-patched"
DIST="$ROOT/local_rebuild/dist"
PRIVATE="$ROOT/local_rebuild/private"
LOGS="$ROOT/local_rebuild/logs"
HTTP_SMOKE="${LOCALTEST_HTTP_SMOKE:-0}"
PACKAGE="${LOCALTEST_PACKAGE:-com.alibaba.android.rimet.localtest}"
APP_LABEL="${LOCALTEST_APP_LABEL:-}"
OVERLAY_OFFSET_DP="${LOCALTEST_OVERLAY_OFFSET_DP:-0}"
UC_AUTH_BYPASS="${LOCALTEST_UC_AUTH_BYPASS:-0}"
OLD_PKG_PREFIX="com.alibaba.android.rimet."

# classes25 carries the only UC checkAuthorization call site; round-trip it
# (and only it) when the bypass is requested so default builds stay untouched.
PATCH_DEXS="classes33 classes36 classes37 classes38"
if [[ "$UC_AUTH_BYPASS" == "1" ]]; then
  PATCH_DEXS="classes25 $PATCH_DEXS"
fi

if [[ "$PACKAGE" != "$OLD_PKG_PREFIX"* || "$PACKAGE" == "$OLD_PKG_PREFIX" ]]; then
  printf 'invalid-package-prefix: %s (must start with %s<suffix>)\n' "$PACKAGE" "$OLD_PKG_PREFIX" >&2
  exit 1
fi
VARIANT="${PACKAGE#$OLD_PKG_PREFIX}"

: "${LOCALTEST_SERVER_URL:?set LOCALTEST_SERVER_URL to the backend base URL}"
SERVER_URL="$(PYTHONPATH="$ROOT" python3 -m local_rebuild.patches.backend_config "$LOCALTEST_SERVER_URL")"

if [[ "$HTTP_SMOKE" == "1" ]]; then
  OUTPUT_NAME="dingtalk-$VARIANT-smoke"
else
  OUTPUT_NAME="dingtalk-$VARIANT"
fi
FINAL_APK="$DIST/$OUTPUT_NAME.apk" # e.g. dingtalk-localtest-smoke.apk for default smoke
UNSIGNED_APK="$DIST/$OUTPUT_NAME-unsigned.apk"
ALIGNED_APK="$DIST/$OUTPUT_NAME-aligned.apk"
METADATA="$DIST/$OUTPUT_NAME.backend-url"

mkdir -p "$SOURCE" "$DIST" "$PRIVATE" "$LOGS"
cmp -s "$ROOT/working.apk" "$INPUT"
rm -rf "$DECODED" "$DEX_INPUT" "$SMALI_ROOT" "$DEX_PATCHED"
mkdir -p "$DEX_INPUT" "$SMALI_ROOT" "$DEX_PATCHED"
rm -f "$UNSIGNED_APK" "$ALIGNED_APK" "$FINAL_APK" "$METADATA"

java -jar "$APKTOOL" d -f -s "$INPUT" -o "$DECODED" \
  >"$LOGS/build-01-decode.log" 2>&1
cp "$DECODED/AndroidManifest.xml" "$DECODED/AndroidManifest.xml.before-localtest"

MANIFEST_ARGS=(--new-package "$PACKAGE")
if [[ -n "$APP_LABEL" ]]; then
  MANIFEST_ARGS+=(--app-label "$APP_LABEL")
fi
PYTHONPATH="$ROOT" python3 "$ROOT/local_rebuild/patches/patch_manifest.py" \
  "${MANIFEST_ARGS[@]}" "$DECODED/AndroidManifest.xml" >"$LOGS/build-02-manifest.json"

DEX_EXTRACT_ARGS=()
for dex in $PATCH_DEXS; do
  DEX_EXTRACT_ARGS+=("$dex.dex")
done
unzip -j -o "$INPUT" "${DEX_EXTRACT_ARGS[@]}" -d "$DEX_INPUT" \
  >"$LOGS/build-03-extract-dex.log"
for dex in $PATCH_DEXS; do
  mkdir -p "$SMALI_ROOT/$dex"
  java -cp "$SMALI_CP" org.jf.baksmali.Main d "$DEX_INPUT/$dex.dex" \
    -o "$SMALI_ROOT/$dex" >>"$LOGS/build-04-baksmali.log" 2>&1
done

SMALI_PATCH_ARGS=(--new-package "$PACKAGE")
if [[ "$HTTP_SMOKE" == "1" ]]; then
  SMALI_PATCH_ARGS+=(--http-smoke)
fi
if [[ "$OVERLAY_OFFSET_DP" != "0" ]]; then
  SMALI_PATCH_ARGS+=(--overlay-offset-dp "$OVERLAY_OFFSET_DP")
fi
if [[ "$UC_AUTH_BYPASS" == "1" ]]; then
  SMALI_PATCH_ARGS+=(--uc-auth-bypass)
fi
PYTHONPATH="$ROOT" python3 "$ROOT/local_rebuild/patches/patch_smali.py" \
  --server-url "$SERVER_URL" "${SMALI_PATCH_ARGS[@]}" "$SMALI_ROOT" \
  >"$LOGS/build-05-smali-patch.log"

for dex in $PATCH_DEXS; do
  java -cp "$SMALI_CP" org.jf.smali.Main a "$SMALI_ROOT/$dex" \
    -o "$DEX_PATCHED/$dex.dex" >>"$LOGS/build-06-smali.log" 2>&1
  test -s "$DEX_PATCHED/$dex.dex"
  cp "$DEX_PATCHED/$dex.dex" "$DECODED/$dex.dex"
done

java -jar "$APKTOOL" b -f "$DECODED" \
  -o "$UNSIGNED_APK" >"$LOGS/build-07-apktool-build.log" 2>&1
zipalign -f -p 4 "$UNSIGNED_APK" \
  "$ALIGNED_APK" >"$LOGS/build-08-zipalign.log" 2>&1
zipalign -c -p 4 "$ALIGNED_APK" \
  >>"$LOGS/build-08-zipalign.log" 2>&1

PASSWORD_FILE="$PRIVATE/signing-password"
KEYSTORE="$PRIVATE/localtest.keystore"
if [[ ! -f "$PASSWORD_FILE" ]]; then
  umask 077
  python3 -c 'import secrets; print(secrets.token_urlsafe(24))' >"$PASSWORD_FILE"
fi
chmod 600 "$PASSWORD_FILE"
export LOCALTEST_KEY_PASS="$(<"$PASSWORD_FILE")"

if [[ ! -f "$KEYSTORE" ]]; then
  keytool -genkeypair -noprompt \
    -keystore "$KEYSTORE" \
    -storetype PKCS12 \
    -alias localtest \
    -keyalg RSA \
    -keysize 2048 \
    -validity 3650 \
    -dname "CN=DingTalk Localtest, OU=Local Analysis, O=Local Analysis, C=CN" \
    -storepass:env LOCALTEST_KEY_PASS \
    -keypass:env LOCALTEST_KEY_PASS >"$LOGS/build-09-keytool.log" 2>&1
fi

apksigner sign \
  --ks "$KEYSTORE" \
  --ks-key-alias localtest \
  --ks-pass env:LOCALTEST_KEY_PASS \
  --key-pass env:LOCALTEST_KEY_PASS \
  --out "$FINAL_APK" \
  "$ALIGNED_APK" >"$LOGS/build-10-sign.log" 2>&1

apksigner verify --verbose "$FINAL_APK" \
  >"$LOGS/build-11-signature-verify.log" 2>&1
printf '%s\n' "$SERVER_URL" >"$METADATA"
printf 'apk-build-ok\n'
