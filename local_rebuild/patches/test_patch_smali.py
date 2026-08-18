from pathlib import Path

import pytest

from local_rebuild.patches.patch_smali import (
    CREATOR_PROXY_MARKER,
    CREATOR_PROXY_OPTIONAL_BLOCK,
    HTTP_SMOKE_ANCHOR,
    HTTP_SMOKE_INSERTION,
    PATCHES,
    PatchSpec,
    patch_creator_proxy,
    patch_all,
    patch_http_smoke,
    patch_literal,
    patch_tree,
    verify_creator_proxy,
    verify_all,
    verify_http_smoke,
    verify_tree,
)


def test_patch_literal_replaces_exact_expected_count(tmp_path):
    path = tmp_path / "Example.smali"
    path.write_text(
        'const-string v0, "old-value"\nconst-string v1, "old-value"\n',
        encoding="utf-8",
    )

    patch_literal(path, "old-value", "new-value", 2)

    text = path.read_text(encoding="utf-8")
    assert text.count('"new-value"') == 2
    assert '"old-value"' not in text


def test_patch_literal_fails_closed_on_count_mismatch(tmp_path):
    path = tmp_path / "Example.smali"
    path.write_text(
        '.field private static final VALUE:Ljava/lang/String; = "old-value"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expected 2"):
        patch_literal(path, "old-value", "new-value", 2)

    assert '"old-value"' in path.read_text(encoding="utf-8")


def test_patch_tree_handles_field_and_const_string_literals(tmp_path):
    contents = {
        "classes36/com/example/Http.smali": 'const-string v0, "remote"\n',
        "classes37/com/example/Module.smali": (
            '.field private static final TARGET:Ljava/lang/String; = "old.package"\n'
        ),
    }
    for relative_path, content in contents.items():
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    specs = (
        PatchSpec(Path("classes36/com/example/Http.smali"), "remote", "local", 1),
        PatchSpec(
            Path("classes37/com/example/Module.smali"),
            "old.package",
            "new.package",
            1,
        ),
    )

    patch_tree(tmp_path, specs)

    assert '"local"' in (tmp_path / specs[0].relative_path).read_text(encoding="utf-8")
    assert '"new.package"' in (tmp_path / specs[1].relative_path).read_text(
        encoding="utf-8"
    )


def test_known_package_patch_specs_match_actual_compiler_layout():
    package_specs = {
        str(spec.relative_path): spec.expected_count
        for spec in PATCHES
        if spec.original == "com.alibaba.android.rimet"
    }

    assert package_specs == {
        "classes37/com/dingtalk/groupbill/ModuleLoader.smali": 2,
        "classes37/com/dingtalk/groupbill/HookMain.smali": 1,
        "classes37/com/dingtalk/groupbill/GroupBillHooks$3.smali": 1,
        "classes38/com/pineloader/PineLoader.smali": 1,
    }


def test_verify_tree_checks_replacement_counts_and_rejects_originals(tmp_path):
    path = tmp_path / "classes36/com/example/Http.smali"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('const-string v0, "local"\n', encoding="utf-8")
    specs = (PatchSpec(Path("classes36/com/example/Http.smali"), "remote", "local", 1),)

    verify_tree(tmp_path, specs)

    path.write_text('const-string v0, "remote"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="verification failed"):
        verify_tree(tmp_path, specs)


def test_creator_proxy_patch_removes_only_optional_paired_creator_cache(tmp_path):
    path = tmp_path / "classes33/com/pandora/core/CreatorProxy.smali"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'before\nconst-string v5, "CREATOR"\n'
        'const-string v6, "mCreators"\n'
        'const-string v7, "android.content.pm.PackageInfo$1"\n'
        + CREATOR_PROXY_OPTIONAL_BLOCK
        + "after\n",
        encoding="utf-8",
    )

    patch_creator_proxy(tmp_path)
    verify_creator_proxy(tmp_path)

    text = path.read_text(encoding="utf-8")
    assert "before\n" in text
    assert "after\n" in text
    assert "sPairedCreators" not in text
    assert text.count(CREATOR_PROXY_MARKER) == 1


def test_creator_proxy_patch_fails_closed_when_block_is_missing(tmp_path):
    path = tmp_path / "classes33/com/pandora/core/CreatorProxy.smali"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("unrelated\n", encoding="utf-8")

    with pytest.raises(ValueError, match="optional cache block"):
        patch_creator_proxy(tmp_path)


def test_creator_proxy_verification_accepts_reassembled_smali_without_comments(tmp_path):
    path = tmp_path / "classes33/com/pandora/core/CreatorProxy.smali"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        'const-string v0, "CREATOR"\n'
        'const-string v1, "mCreators"\n'
        'const-string v2, "android.content.pm.PackageInfo$1"\n',
        encoding="utf-8",
    )

    verify_creator_proxy(tmp_path)


def test_http_smoke_patch_inserts_one_synthetic_upload_after_module_load(tmp_path):
    path = tmp_path / "classes37/com/dingtalk/groupbill/ModuleLoader.smali"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + HTTP_SMOKE_ANCHOR + "after\n", encoding="utf-8")

    patch_http_smoke(tmp_path)
    verify_http_smoke(tmp_path)

    text = path.read_text(encoding="utf-8")
    assert text.count(HTTP_SMOKE_INSERTION) == 1
    assert text.index(HTTP_SMOKE_INSERTION) < text.index(":try_end_106")


def test_http_smoke_patch_fails_closed_when_anchor_is_missing(tmp_path):
    path = tmp_path / "classes37/com/dingtalk/groupbill/ModuleLoader.smali"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("unrelated\n", encoding="utf-8")

    with pytest.raises(ValueError, match="HTTP smoke anchor"):
        patch_http_smoke(tmp_path)


def test_patch_all_leaves_http_smoke_disabled_by_default(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(
        "local_rebuild.patches.patch_smali.patch_tree",
        lambda root, specs: called.append("tree"),
    )
    monkeypatch.setattr(
        "local_rebuild.patches.patch_smali.patch_creator_proxy",
        lambda root: called.append("creator"),
    )
    monkeypatch.setattr(
        "local_rebuild.patches.patch_smali.patch_http_smoke",
        lambda root: called.append("smoke"),
    )

    patch_all(tmp_path, "https://api.example.com")
    assert called == ["tree", "creator"]


def test_patch_all_can_enable_http_smoke_explicitly(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(
        "local_rebuild.patches.patch_smali.patch_tree",
        lambda root, specs: called.append("tree"),
    )
    monkeypatch.setattr(
        "local_rebuild.patches.patch_smali.patch_creator_proxy",
        lambda root: called.append("creator"),
    )
    monkeypatch.setattr(
        "local_rebuild.patches.patch_smali.patch_http_smoke",
        lambda root: called.append("smoke"),
    )

    patch_all(tmp_path, "https://api.example.com", enable_http_smoke=True)
    assert called == ["tree", "creator", "smoke"]


def test_patch_all_uses_the_configured_backend_url(tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(
        "local_rebuild.patches.patch_smali.patch_tree",
        lambda root, specs: captured.extend(specs),
    )
    monkeypatch.setattr("local_rebuild.patches.patch_smali.patch_creator_proxy", lambda root: None)

    patch_all(tmp_path, server_url="https://API.EXAMPLE.COM/")

    endpoint_spec = next(spec for spec in captured if "HttpReporter" in str(spec.relative_path))
    assert endpoint_spec.replacement == "https://api.example.com"


def test_verify_all_uses_the_configured_backend_url(tmp_path, monkeypatch):
    captured = []
    monkeypatch.setattr(
        "local_rebuild.patches.patch_smali.verify_tree",
        lambda root, specs: captured.extend(specs),
    )
    monkeypatch.setattr("local_rebuild.patches.patch_smali.verify_creator_proxy", lambda root: None)
    monkeypatch.setattr("local_rebuild.patches.patch_smali.verify_http_smoke", lambda root: None)

    verify_all(
        tmp_path,
        server_url="http://192.168.1.10:18722",
        expect_http_smoke=True,
    )

    endpoint_spec = next(spec for spec in captured if "HttpReporter" in str(spec.relative_path))
    assert endpoint_spec.replacement == "http://192.168.1.10:18722"
