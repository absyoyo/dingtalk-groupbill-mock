#!/usr/bin/env bash
# Compile CryptoBox.java -> dex -> smali, drop into tools/android-crypto/cryptobox-smali/
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK="$ROOT/local_rebuild/hook"
TOOLS="$ROOT/local_rebuild/tools/android-crypto"
OUT="$TOOLS/build"
SMALI_OUT="$TOOLS/cryptobox-smali"
JSON_JAR="$TOOLS/json-20240303.jar"
R8_JAR="$TOOLS/r8.jar"
SMALI_CP="$ROOT/local_rebuild/tools/jadx-1.4.7/lib/*"

rm -rf "$OUT" "$SMALI_OUT"
mkdir -p "$OUT/classes" "$OUT/dex"

javac --release 8 -cp "$JSON_JAR:$HOOK/stub" -d "$OUT/classes" \
  "$HOOK/com/dingtalk/groupbill/net/CryptoBox.java"

# Only CryptoBox.class — do not bundle org.json or the HttpReporter stub.
find "$OUT/classes" -name 'HttpReporter.class' -delete
java -cp "$R8_JAR" com.android.tools.r8.D8 \
  --min-api 21 \
  --output "$OUT/dex" \
  $(find "$OUT/classes" -name '*.class')

java -cp "$SMALI_CP" org.jf.baksmali.Main d "$OUT/dex/classes.dex" \
  -o "$SMALI_OUT"

# Sanity: the class file must exist
test -f "$SMALI_OUT/com/dingtalk/groupbill/net/CryptoBox.smali"
echo "compiled: $SMALI_OUT/com/dingtalk/groupbill/net/CryptoBox.smali"
