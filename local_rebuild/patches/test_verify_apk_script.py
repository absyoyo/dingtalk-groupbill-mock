from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VERIFY_SCRIPT = PROJECT_ROOT / "local_rebuild" / "scripts" / "verify_apk.sh"


def test_verify_script_checks_signature_manifest_and_exact_dex_literals():
    source = VERIFY_SCRIPT.read_text(encoding="utf-8")
    assert 'cmp -s "$ROOT/working.apk" "$ROOT/local_rebuild/input/working.apk"' in source
    assert "apksigner verify --verbose" in source
    assert "zipalign -c -p 4" in source
    assert 'unzip -Z1 "$APK" >"$LOGS/verify-00-entries.txt"' in source
    assert 'grep -Fxq \'AndroidManifest.xml\' "$LOGS/verify-00-entries.txt"' in source
    assert "--only-manifest -s" in source
    assert "verify_manifest.py" in source
    assert "classes33.dex classes36.dex classes37.dex classes38.dex" in source
    assert "org.jf.baksmali.Main" in source
    assert "patch_smali.py" in source
    assert "--verify" in source
    assert "apk-static-verify-ok" in source
