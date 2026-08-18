import subprocess
from pathlib import Path

import pytest

from local_rebuild.patches.backend_config import normalize_server_url


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("http://192.168.1.10:18722", "http://192.168.1.10:18722"),
        ("https://api.example.com", "https://api.example.com"),
        (" https://API.EXAMPLE.COM/ ", "https://api.example.com"),
    ],
)
def test_normalize_server_url_accepts_ip_or_domain(value, expected):
    assert normalize_server_url(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "api.example.com",
        "ftp://api.example.com",
        "http://user:pass@api.example.com",
        "https://api.example.com/base",
        "https://api.example.com?debug=1",
        "https://api.example.com#fragment",
        "http://127.0.0.1:18722",
        "http://[::1]:18722",
        "http://localhost:18722",
        "http://0.0.0.0:18722",
        "http://api.example.com:bad",
        "http://api example.com",
        "",
    ],
)
def test_normalize_server_url_rejects_unreachable_or_ambiguous_values(value):
    with pytest.raises(ValueError):
        normalize_server_url(value)


def test_backend_config_cli_prints_normalized_url():
    result = subprocess.run(
        [
            "python3",
            "-m",
            "local_rebuild.patches.backend_config",
            "https://API.EXAMPLE.COM/",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )

    assert result.stdout.strip() == "https://api.example.com"
