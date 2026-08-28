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
    verify_overlay_offset,
    verify_all,
    verify_http_smoke,
    verify_tree,
    patch_overlay_offset,
    patch_uc_auth_bypass,
    verify_uc_auth_bypass,
    OVERLAY_Y_PATH,
    OVERLAY_ANCHOR,
    OVERLAY_MARKER,
    UC_AUTH_PATH,
    UC_AUTH_MARKER,
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


def test_package_patches_and_configured_patches_support_custom_package():
    from local_rebuild.patches.patch_smali import configured_patches, package_patches

    custom_pkg = "com.alibaba.android.rimet.localtest2"
    specs = package_patches(custom_pkg)
    assert len(specs) == 4
    for spec in specs:
        assert spec.replacement == custom_pkg
        assert spec.original == "com.alibaba.android.rimet"

    all_specs = configured_patches("http://192.168.1.10:18722", new_package=custom_pkg)
    pkg_specs_in_all = [s for s in all_specs if s.original == "com.alibaba.android.rimet"]
    assert len(pkg_specs_in_all) == 4
    assert all(s.replacement == custom_pkg for s in pkg_specs_in_all)


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


def test_patch_overlay_offset_inserts_dp_offset_before_conversion(tmp_path):
    path = tmp_path / OVERLAY_Y_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + OVERLAY_ANCHOR + "after\n", encoding="utf-8")

    patch_overlay_offset(tmp_path, 96)
    verify_overlay_offset(tmp_path, 96)

    text = path.read_text(encoding="utf-8")
    assert OVERLAY_MARKER in text
    assert "    add-int/lit16 v3, v3, 96\n" in text
    # offset is applied to the dp-unit base BEFORE the dp() conversion and the y write
    assert text.index("add-int/lit16 v3, v3, 96") < text.index("->dp(")
    assert text.index("->dp(") < text.index("WindowManager$LayoutParams;->y:I")


def test_patch_overlay_offset_fails_closed_when_anchor_missing(tmp_path):
    path = tmp_path / OVERLAY_Y_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("unrelated\n", encoding="utf-8")

    with pytest.raises(ValueError, match="overlay y anchor"):
        patch_overlay_offset(tmp_path, 96)


def test_patch_overlay_offset_is_not_reapplied(tmp_path):
    path = tmp_path / OVERLAY_Y_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + OVERLAY_ANCHOR + "after\n", encoding="utf-8")

    patch_overlay_offset(tmp_path, 96)
    with pytest.raises(ValueError, match="already applied"):
        patch_overlay_offset(tmp_path, 96)


def test_patch_overlay_offset_rejects_non_positive(tmp_path):
    path = tmp_path / OVERLAY_Y_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + OVERLAY_ANCHOR + "after\n", encoding="utf-8")

    with pytest.raises(ValueError, match="positive"):
        patch_overlay_offset(tmp_path, 0)


def test_verify_overlay_offset_rejects_unpatched(tmp_path):
    path = tmp_path / OVERLAY_Y_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + OVERLAY_ANCHOR + "after\n", encoding="utf-8")

    with pytest.raises(ValueError, match="overlay offset verification failed"):
        verify_overlay_offset(tmp_path, 96)


def test_verify_overlay_offset_accepts_round_tripped_hex_without_marker(tmp_path):
    # After smali->dex->baksmali the comment marker is stripped and the literal is
    # rendered in hex (96 -> 0x60). verify must still accept this real-world form.
    round_tripped = (
        "    xor-int/lit16 v3, v3, -0x19f\n"
        "\n"
        "    add-int/lit16 v3, v3, 0x60\n"
        "\n"
        "    invoke-static {p0, v3}, Lcom/dingtalk/groupbill/ui/OverlayBanner;->dp(Landroid/content/Context;I)I\n"
        "\n"
        "    move-result v3\n"
        "\n"
        "    iput v3, v5, Landroid/view/WindowManager$LayoutParams;->y:I\n"
    )
    path = tmp_path / OVERLAY_Y_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + round_tripped + "after\n", encoding="utf-8")

    verify_overlay_offset(tmp_path, 96)


def test_verify_overlay_offset_rejects_misplaced_offset(tmp_path):
    # add-int after the dp() conversion would offset px (wrong), verify must reject.
    misplaced = (
        "    xor-int/lit16 v3, v3, -0x19f\n"
        "\n"
        "    invoke-static {p0, v3}, Lcom/dingtalk/groupbill/ui/OverlayBanner;->dp(Landroid/content/Context;I)I\n"
        "\n"
        "    move-result v3\n"
        "\n"
        "    add-int/lit16 v3, v3, 0x60\n"
        "\n"
        "    iput v3, v5, Landroid/view/WindowManager$LayoutParams;->y:I\n"
    )
    path = tmp_path / OVERLAY_Y_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + misplaced + "after\n", encoding="utf-8")

    with pytest.raises(ValueError, match="wrong position"):
        verify_overlay_offset(tmp_path, 96)


def test_patch_all_skips_overlay_offset_by_default(tmp_path, monkeypatch):
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
        "local_rebuild.patches.patch_smali.patch_overlay_offset",
        lambda root, dp: called.append("overlay"),
    )

    patch_all(tmp_path, "https://api.example.com")
    assert called == ["tree", "creator"]


def test_patch_all_applies_overlay_offset_when_positive(tmp_path, monkeypatch):
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
        "local_rebuild.patches.patch_smali.patch_overlay_offset",
        lambda root, dp: called.append(("overlay", dp)),
    )

    patch_all(tmp_path, "https://api.example.com", overlay_offset_dp=96)
    assert ("overlay", 96) in called


UC_AUTH_FIXTURE_METHOD = '''.method public static a([Ljava/lang/String;Z)V
    .registers 5

    const v0, 0x40e2c1d

    invoke-static {v0}, Lcom/uc/webview/base/timing/TraceEvent;->scoped(I)Lcom/uc/webview/base/timing/TraceEvent;

    move-result-object v0

    :try_start_7
    invoke-static {}, Lcom/uc/webview/internal/interfaces/IStartupController$Instance;->get()Lcom/uc/webview/internal/interfaces/IStartupController;

    move-result-object v1

    :cond_23
    invoke-static {}, Lcom/uc/webview/base/EnvInfo;->getContext()Landroid/content/Context;

    move-result-object p1

    invoke-interface {v1, p1, p0}, Lcom/uc/webview/internal/interfaces/IStartupController;->checkAuthorization(Landroid/content/Context;[Ljava/lang/String;)V
    :try_end_2a
    .catchall {:try_start_7 .. :try_end_2a} :catchall_30

    if-eqz v0, :cond_2f

    invoke-virtual {v0}, Lcom/uc/webview/base/timing/TraceEvent;->close()V

    :cond_2f
    return-void

    :catchall_30
    move-exception p0

    if-eqz v0, :cond_3b

    invoke-virtual {v0}, Lcom/uc/webview/base/timing/TraceEvent;->close()V

    :cond_3b
    goto :goto_3b

    :goto_3b
    throw p0
.end method
'''


def write_uc_auth_fixture(tmp_path):
    path = tmp_path / UC_AUTH_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + UC_AUTH_FIXTURE_METHOD + "after\n", encoding="utf-8")
    return path


def test_patch_uc_auth_bypass_replaces_invoke_with_nop(tmp_path):
    path = write_uc_auth_fixture(tmp_path)

    patch_uc_auth_bypass(tmp_path)
    verify_uc_auth_bypass(tmp_path)

    text = path.read_text(encoding="utf-8")
    assert UC_AUTH_MARKER in text
    assert "    nop\n" in text
    assert "checkAuthorization" not in text
    # method body and its tail survive untouched
    assert ".method public static a([Ljava/lang/String;Z)V" in text
    assert ":try_end_2a" in text
    assert ".end method" in text


def test_patch_uc_auth_bypass_fails_closed_when_invoke_missing(tmp_path):
    path = tmp_path / UC_AUTH_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("unrelated\n", encoding="utf-8")

    with pytest.raises(ValueError, match="uc auth anchor"):
        patch_uc_auth_bypass(tmp_path)


def test_patch_uc_auth_bypass_is_not_reapplied(tmp_path):
    write_uc_auth_fixture(tmp_path)

    patch_uc_auth_bypass(tmp_path)
    with pytest.raises(ValueError, match="already applied"):
        patch_uc_auth_bypass(tmp_path)


def test_verify_uc_auth_bypass_rejects_unpatched(tmp_path):
    write_uc_auth_fixture(tmp_path)

    with pytest.raises(ValueError, match="uc auth verification failed"):
        verify_uc_auth_bypass(tmp_path)


def test_verify_uc_auth_bypass_accepts_round_tripped_nop_without_marker(tmp_path):
    # smali->dex->baksmali strips the marker comment; the nop stays and the
    # checkAuthorization method reference disappears from the string pool.
    round_tripped = UC_AUTH_FIXTURE_METHOD.replace(
        "    invoke-interface {v1, p1, p0}, "
        "Lcom/uc/webview/internal/interfaces/IStartupController;->checkAuthorization"
        "(Landroid/content/Context;[Ljava/lang/String;)V\n",
        "    nop\n",
    )
    path = tmp_path / UC_AUTH_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("before\n" + round_tripped + "after\n", encoding="utf-8")

    verify_uc_auth_bypass(tmp_path)


def test_patch_all_skips_uc_auth_bypass_by_default(tmp_path, monkeypatch):
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
        "local_rebuild.patches.patch_smali.patch_uc_auth_bypass",
        lambda root: called.append("uc"),
    )

    patch_all(tmp_path, "https://api.example.com")
    assert called == ["tree", "creator"]


def test_patch_all_applies_uc_auth_bypass_when_enabled(tmp_path, monkeypatch):
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
        "local_rebuild.patches.patch_smali.patch_uc_auth_bypass",
        lambda root: called.append("uc"),
    )

    patch_all(tmp_path, "https://api.example.com", uc_auth_bypass=True)
    assert "uc" in called
