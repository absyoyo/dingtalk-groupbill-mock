from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "local_rebuild" / "scripts" / "frida_http_smoke.js"


def test_frida_smoke_uses_only_synthetic_data_and_local_endpoint():
    source = SCRIPT.read_text(encoding="utf-8")
    assert "com.dingtalk.groupbill.net.HttpReporter" in source
    assert '"http://127.0.0.1:18722"' in source
    assert "HttpReporter.uploadOrder" in source
    assert '"local-debug-user"' in source
    assert '"local-debug-order"' in source
    assert '"local-debug-pay"' in source
    assert "frida-http-smoke-dispatched" in source
    assert "47.239.160.117" not in source
