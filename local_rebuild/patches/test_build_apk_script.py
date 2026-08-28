from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = PROJECT_ROOT / "local_rebuild" / "scripts" / "build_apk.sh"
VERIFY_SCRIPT = PROJECT_ROOT / "local_rebuild" / "scripts" / "verify_apk.sh"
BACKEND_WRAPPER = PROJECT_ROOT / "local_rebuild" / "scripts" / "build_for_backend.sh"


def test_build_script_rebuilds_resources_but_patches_only_injected_dex():
    source = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "apktool_3.0.3.jar" in source
    assert "local_rebuild/tools/jadx-1.4.7/lib/*" in source
    assert ' d -f -s ' in source
    assert ' d -f -r -s ' not in source
    assert "--only-manifest" not in source
    assert 'PATCH_DEXS="classes33 classes36 classes37 classes38"' in source
    # classes25 (UC auth bypass target) joins the patch set only when requested
    assert "classes25 $PATCH_DEXS" in source or "classes25 $VERIFY_DEXS" in source
    assert "patch_manifest.py" in source
    assert "patch_smali.py" in source
    assert "org.jf.baksmali.Main" in source
    assert "org.jf.smali.Main" in source
    assert "zipalign -f -p 4" in source
    assert "apksigner sign" in source


def test_build_script_keeps_signing_password_out_of_process_arguments():
    source = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "signing-password" in source
    assert "-storepass:env LOCALTEST_KEY_PASS" in source
    assert "-keypass:env LOCALTEST_KEY_PASS" in source
    assert "--ks-pass env:LOCALTEST_KEY_PASS" in source
    assert "--key-pass env:LOCALTEST_KEY_PASS" in source
    assert "--ks-pass pass:" not in source
    assert "--key-pass pass:" not in source


def test_build_script_verifies_input_and_final_signature():
    source = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert 'cmp -s "$ROOT/working.apk" "$INPUT"' in source
    assert "apksigner verify --verbose" in source
    assert "apk-build-ok" in source


def test_build_script_enables_synthetic_http_only_through_explicit_environment_flag():
    source = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert 'LOCALTEST_HTTP_SMOKE:-0' in source
    assert "--http-smoke" in source


def test_smoke_build_and_verification_use_a_distinct_artifact():
    build_source = BUILD_SCRIPT.read_text(encoding="utf-8")
    verify_source = VERIFY_SCRIPT.read_text(encoding="utf-8")

    for source in (build_source, verify_source):
        assert "dingtalk-localtest-smoke.apk" in source
        assert 'LOCALTEST_HTTP_SMOKE:-0' in source


def test_build_and_verify_require_one_canonical_backend_url():
    for script in (BUILD_SCRIPT, VERIFY_SCRIPT):
        source = script.read_text(encoding="utf-8")
        assert "LOCALTEST_SERVER_URL" in source
        assert "local_rebuild.patches.backend_config" in source
        assert '--server-url "$SERVER_URL"' in source
        assert ".backend-url" in source


def test_backend_wrapper_builds_and_verifies_default_or_smoke_artifacts():
    source = BACKEND_WRAPPER.read_text(encoding="utf-8")
    assert "LOCALTEST_SERVER_URL" in source
    assert "--smoke" in source
    assert "build_apk.sh" in source
    assert "verify_apk.sh" in source
    assert "backend-apk-ready" in source
