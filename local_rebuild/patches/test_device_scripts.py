from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT_ROOT / "local_rebuild" / "scripts"
PHONE_BUILD = SCRIPTS / "build_for_connected_phone.sh"


def test_device_setup_installs_only_localtest_and_preserves_official_package():
    source = (SCRIPTS / "device_setup.sh").read_text(encoding="utf-8")
    assert "127.0.0.1:18722/health" not in source
    assert "dingtalk-localtest.backend-url" in source
    assert "adb reverse --remove tcp:18722" in source
    assert "adb-reverse-removal-failed" in source
    assert "adb reverse tcp:18722 tcp:18722" not in source
    assert 'adb install -r "$APK"' in source
    assert 'adb shell pm path "$OFFICIAL"' in source
    assert 'adb shell pm path "$LOCALTEST"' in source
    assert '"$LOCALTEST/com.alibaba.android.rimet.biz.LaunchHomeActivity"' in source
    assert "adb uninstall" not in source
    assert "device-setup-ok" in source


def test_device_cleanup_never_uninstalls_or_stops_official_package():
    source = (SCRIPTS / "device_cleanup.sh").read_text(encoding="utf-8")
    assert "am force-stop com.alibaba.android.rimet.localtest" in source
    assert "adb reverse --remove tcp:18722" in source
    assert "adb uninstall" not in source
    assert "am force-stop com.alibaba.android.rimet\n" not in source
    assert "device-cleanup-ok" in source


def test_connected_phone_builder_selects_the_host_route_to_the_phone():
    source = PHONE_BUILD.read_text(encoding="utf-8")
    assert "cmd wifi status" in source
    assert "ip -4 -o addr show scope global" in source
    assert "ip -4 route get" in source
    assert "build_for_backend.sh" in source
    assert "18722" in source
    assert "--smoke" in source
