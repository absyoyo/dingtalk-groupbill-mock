from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from local_rebuild.patches.backend_config import normalize_server_url


OLD_PACKAGE = "com.alibaba.android.rimet"
NEW_PACKAGE = "com.alibaba.android.rimet.localtest"
OLD_ENDPOINT = "http://47.239.160.117:18722"
CREATOR_PROXY_PATH = Path("classes33/com/pandora/core/CreatorProxy.smali")
CREATOR_PROXY_MARKER = (
    "    # localtest: the paired creator cache is optional on this Android build.\n"
)
CREATOR_PROXY_OPTIONAL_BLOCK = '''    .line 63
    const-class v2, Landroid/os/Parcel;

    const-string v4, "sPairedCreators"

    invoke-static {v2, v4}, Lcom/pandora/core/CreatorProxy;->findField(Ljava/lang/Class;Ljava/lang/String;)Ljava/lang/reflect/Field;

    move-result-object v2

    invoke-virtual {v2, v0}, Ljava/lang/reflect/Field;->get(Ljava/lang/Object;)Ljava/lang/Object;

    move-result-object v0

    check-cast v0, Ljava/util/Map;

    .line 64
    invoke-interface {v0}, Ljava/util/Map;->clear()V

'''
HTTP_SMOKE_PATH = Path("classes37/com/dingtalk/groupbill/ModuleLoader.smali")
HTTP_SMOKE_ANCHOR = '''    invoke-static {v6, v7}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I
    :try_end_106
'''
HTTP_SMOKE_INSERTION = '''    const-string v6, "local-debug-user"

    const-string v7, "local-debug-order"

    const-string v8, "local-debug-pay"

    const-wide/high16 v9, 0x3ff0000000000000L

    invoke-static/range {v6 .. v10}, Lcom/dingtalk/groupbill/net/HttpReporter;->uploadOrder(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;D)V

'''
# Coexisting variants share one injected module, so the system overlay banner
# (WindowManager$LayoutParams gravity=TOP|CENTER + fixed y) lands at the same
# spot for every variant and overlaps. To separate them, a second variant build
# adds a dp-unit offset to the y base *before* the dp()->px conversion, which is
# density-correct and reuses v3 (no extra register needed).
OVERLAY_Y_PATH = Path("classes37/com/dingtalk/groupbill/ui/OverlayBanner.smali")
OVERLAY_MARKER = "    # localtest-variant overlay stack offset\n"
OVERLAY_ANCHOR = (
    "    xor-int/lit16 v3, v3, -0x19f\n"
    "\n"
    "    invoke-static {p0, v3}, Lcom/dingtalk/groupbill/ui/OverlayBanner;->dp(Landroid/content/Context;I)I\n"
    "\n"
    "    move-result v3\n"
    "\n"
    "    iput v3, v5, Landroid/view/WindowManager$LayoutParams;->y:I\n"
)
OVERLAY_XOR_LINE = "    xor-int/lit16 v3, v3, -0x19f\n"
OVERLAY_DP_INVOKE = (
    "    invoke-static {p0, v3}, Lcom/dingtalk/groupbill/ui/OverlayBanner;->dp(Landroid/content/Context;I)I\n"
)
# The UC (U4) WebView core refuses to initialize in a repackaged app: its
# com.uc.sdk_glue auth layer expects MD5(packageName + SHA-1(signing cert))
# bound to the official DingTalk identity, so every coexistence clone fails
# with COMPATIABLE_INVALID_APP_KEY and all H5 lightapps (群收款 included)
# fall to CommonErrorActivity with OPEN_FAIL_UC_FAIL. The only call site of
# IStartupController.checkAuthorization lives in our patchable classes25.dex;
# neutralizing that single invoke-interface with a nop lets the core start.
UC_AUTH_PATH = Path("classes25/com/uc/webview/internal/setup/verify/d.smali")
UC_AUTH_MARKER = "    # localtest: uc auth bypass\n"
UC_AUTH_INVOKE = (
    "    invoke-interface {v1, p1, p0}, "
    "Lcom/uc/webview/internal/interfaces/IStartupController;->checkAuthorization"
    "(Landroid/content/Context;[Ljava/lang/String;)V\n"
)
UC_AUTH_METHOD_REF = "IStartupController;->checkAuthorization("


@dataclass(frozen=True)
class PatchSpec:
    """Describe one exact literal replacement in one injected smali file."""

    relative_path: Path
    original: str
    replacement: str
    expected_count: int


def package_patches(new_package: str) -> tuple[PatchSpec, ...]:
    """Return the smali literal replacement specs targeting a specific package identity."""
    return (
        PatchSpec(
            Path("classes37/com/dingtalk/groupbill/ModuleLoader.smali"),
            OLD_PACKAGE,
            new_package,
            2,
        ),
        PatchSpec(
            Path("classes37/com/dingtalk/groupbill/HookMain.smali"),
            OLD_PACKAGE,
            new_package,
            1,
        ),
        PatchSpec(
            Path("classes37/com/dingtalk/groupbill/GroupBillHooks$3.smali"),
            OLD_PACKAGE,
            new_package,
            1,
        ),
        PatchSpec(
            Path("classes38/com/pineloader/PineLoader.smali"),
            OLD_PACKAGE,
            new_package,
            1,
        ),
    )


PATCHES = package_patches(NEW_PACKAGE)


def configured_patches(server_url: str, new_package: str = NEW_PACKAGE) -> tuple[PatchSpec, ...]:
    """Return all exact smali replacements for one normalized backend URL."""
    endpoint_patch = PatchSpec(
        Path("classes36/com/dingtalk/groupbill/net/HttpReporter.smali"),
        OLD_ENDPOINT,
        normalize_server_url(server_url),
        1,
    )
    return (endpoint_patch, *package_patches(new_package))


def patch_literal(
    path: str | Path,
    original: str,
    replacement: str,
    expected_count: int,
) -> None:
    """Replace a quoted smali literal only when its evidence-backed count matches."""
    smali_path = Path(path)
    text = smali_path.read_text(encoding="utf-8")
    original_token = f'"{original}"'
    replacement_token = f'"{replacement}"'
    original_count = text.count(original_token)
    if original_count != expected_count:
        raise ValueError(
            f"{smali_path}: expected {expected_count} occurrences of "
            f"{original!r}, found {original_count}"
        )
    replacement_count = text.count(replacement_token)
    if replacement_count:
        raise ValueError(
            f"{smali_path}: replacement literal already appears {replacement_count} times"
        )

    updated = text.replace(original_token, replacement_token)
    if updated.count(original_token) != 0:
        raise ValueError(f"{smali_path}: original literal remains after replacement")
    if updated.count(replacement_token) != expected_count:
        raise ValueError(f"{smali_path}: replacement count verification failed")
    smali_path.write_text(updated, encoding="utf-8")


def patch_tree(
    root: str | Path,
    specs: Iterable[PatchSpec] = PATCHES,
) -> None:
    """Apply every known injected-module literal patch beneath a smali root."""
    smali_root = Path(root)
    for spec in specs:
        patch_literal(
            smali_root / spec.relative_path,
            spec.original,
            spec.replacement,
            spec.expected_count,
        )


def patch_creator_proxy(root: str | Path) -> None:
    """Remove the one Android-version-specific sPairedCreators cache clear block."""
    path = Path(root) / CREATOR_PROXY_PATH
    text = path.read_text(encoding="utf-8")
    block_count = text.count(CREATOR_PROXY_OPTIONAL_BLOCK)
    if block_count != 1:
        raise ValueError(
            f"{path}: expected one optional cache block, found {block_count}"
        )
    if CREATOR_PROXY_MARKER in text:
        raise ValueError(f"{path}: creator proxy patch marker already exists")
    path.write_text(
        text.replace(CREATOR_PROXY_OPTIONAL_BLOCK, CREATOR_PROXY_MARKER),
        encoding="utf-8",
    )


def verify_creator_proxy(root: str | Path) -> None:
    """Verify the optional cache is absent while the core proxy operations remain."""
    path = Path(root) / CREATOR_PROXY_PATH
    text = path.read_text(encoding="utf-8")
    required_literals = ('"CREATOR"', '"mCreators"', '"android.content.pm.PackageInfo$1"')
    if "sPairedCreators" in text or any(
        text.count(literal) != 1 for literal in required_literals
    ):
        raise ValueError(f"{path}: creator proxy compatibility verification failed")


def patch_http_smoke(root: str | Path) -> None:
    """Insert one localtest-only synthetic HTTP report after successful module loading."""
    path = Path(root) / HTTP_SMOKE_PATH
    text = path.read_text(encoding="utf-8")
    anchor_count = text.count(HTTP_SMOKE_ANCHOR)
    if anchor_count != 1:
        raise ValueError(f"{path}: expected one HTTP smoke anchor, found {anchor_count}")
    if "local-debug-pay" in text:
        raise ValueError(f"{path}: HTTP smoke insertion already exists")
    replacement = HTTP_SMOKE_ANCHOR.replace(
        "    :try_end_106\n",
        HTTP_SMOKE_INSERTION + "    :try_end_106\n",
    )
    path.write_text(text.replace(HTTP_SMOKE_ANCHOR, replacement), encoding="utf-8")


def verify_http_smoke(root: str | Path) -> None:
    """Verify the final smali contains one complete synthetic HTTP smoke invocation."""
    path = Path(root) / HTTP_SMOKE_PATH
    text = path.read_text(encoding="utf-8")
    required = (
        '"local-debug-user"',
        '"local-debug-order"',
        '"local-debug-pay"',
        "Lcom/dingtalk/groupbill/net/HttpReporter;->uploadOrder(Ljava/lang/String;Ljava/lang/String;Ljava/lang/String;D)V",
    )
    if any(text.count(value) != 1 for value in required):
        raise ValueError(f"{path}: HTTP smoke verification failed")


def _overlay_patched_block(offset_dp: int) -> str:
    """Return the overlay y anchor with a dp-unit offset added before the dp() conversion."""
    return OVERLAY_ANCHOR.replace(
        OVERLAY_XOR_LINE,
        OVERLAY_XOR_LINE + "\n" + OVERLAY_MARKER + f"    add-int/lit16 v3, v3, {offset_dp}\n",
    )


def patch_overlay_offset(root: str | Path, offset_dp: int) -> None:
    """Shift the system overlay banner down by offset_dp so coexisting variants do not overlap."""
    if offset_dp <= 0:
        raise ValueError(f"overlay offset must be positive, found {offset_dp}")
    path = Path(root) / OVERLAY_Y_PATH
    text = path.read_text(encoding="utf-8")
    if OVERLAY_MARKER in text:
        raise ValueError(f"{path}: overlay offset already applied")
    anchor_count = text.count(OVERLAY_ANCHOR)
    if anchor_count != 1:
        raise ValueError(f"{path}: expected one overlay y anchor, found {anchor_count}")
    path.write_text(
        text.replace(OVERLAY_ANCHOR, _overlay_patched_block(offset_dp)),
        encoding="utf-8",
    )


def verify_overlay_offset(root: str | Path, offset_dp: int) -> None:
    """Verify the overlay y base was shifted by exactly offset_dp once, before the dp() conversion.

    The check must survive a smali->dex->baksmali round trip, which strips comments and
    re-renders integer literals in hex, so it matches the add-int instruction (decimal or
    hex form) and its position relative to the unique WindowManager y write, not the marker.
    """
    path = Path(root) / OVERLAY_Y_PATH
    text = path.read_text(encoding="utf-8")
    candidates = (
        f"    add-int/lit16 v3, v3, {offset_dp}\n",
        f"    add-int/lit16 v3, v3, 0x{offset_dp:x}\n",
    )
    total = sum(text.count(candidate) for candidate in candidates)
    add_line = next((candidate for candidate in candidates if candidate in text), None)
    if add_line is None or total != 1:
        raise ValueError(f"{path}: overlay offset verification failed")
    xor_idx = text.find(OVERLAY_XOR_LINE)
    add_idx = text.find(add_line)
    dp_idx = text.find(OVERLAY_DP_INVOKE, add_idx)
    y_idx = text.find("    iput v3, v5, Landroid/view/WindowManager$LayoutParams;->y:I\n")
    if not (0 <= xor_idx < add_idx < dp_idx < y_idx):
        raise ValueError(f"{path}: overlay offset applied at wrong position")


def patch_uc_auth_bypass(root: str | Path) -> None:
    """Neutralize the only checkAuthorization call site so the U4 core starts in clones.

    Testing-only measure for the local repackaged clone: it bypasses a third-party
    SDK authorization check and must never be used to distribute or run against
    production authorization systems.
    """
    path = Path(root) / UC_AUTH_PATH
    text = path.read_text(encoding="utf-8")
    invoke_count = text.count(UC_AUTH_INVOKE)
    if invoke_count == 0:
        if UC_AUTH_MARKER in text:
            raise ValueError(f"{path}: uc auth bypass already applied")
        raise ValueError(f"{path}: expected one uc auth anchor, found 0")
    if invoke_count != 1:
        raise ValueError(f"{path}: expected one uc auth anchor, found {invoke_count}")
    path.write_text(
        text.replace(UC_AUTH_INVOKE, UC_AUTH_MARKER + "    nop\n"),
        encoding="utf-8",
    )


def verify_uc_auth_bypass(root: str | Path) -> None:
    """Verify the checkAuthorization invoke is gone (marker comments do not survive round trips)."""
    path = Path(root) / UC_AUTH_PATH
    text = path.read_text(encoding="utf-8")
    if UC_AUTH_METHOD_REF in text:
        raise ValueError(f"{path}: uc auth verification failed")


def verify_tree(
    root: str | Path,
    specs: Iterable[PatchSpec] = PATCHES,
) -> None:
    """Verify every rebuilt smali target contains only the replacement literal."""
    smali_root = Path(root)
    for spec in specs:
        path = smali_root / spec.relative_path
        text = path.read_text(encoding="utf-8")
        original_count = text.count(f'"{spec.original}"')
        replacement_count = text.count(f'"{spec.replacement}"')
        if original_count != 0 or replacement_count != spec.expected_count:
            raise ValueError(
                f"{path}: verification failed; original={original_count}, "
                f"replacement={replacement_count}, expected={spec.expected_count}"
            )


def patch_all(
    root: str | Path,
    server_url: str,
    new_package: str = NEW_PACKAGE,
    *,
    enable_http_smoke: bool = False,
    overlay_offset_dp: int = 0,
    uc_auth_bypass: bool = False,
) -> None:
    """Apply all literal and Android-version compatibility patches."""
    patch_tree(root, configured_patches(server_url, new_package))
    patch_creator_proxy(root)
    if enable_http_smoke:
        patch_http_smoke(root)
    if overlay_offset_dp > 0:
        patch_overlay_offset(root, overlay_offset_dp)
    if uc_auth_bypass:
        patch_uc_auth_bypass(root)


def verify_all(
    root: str | Path,
    server_url: str,
    new_package: str = NEW_PACKAGE,
    *,
    expect_http_smoke: bool = False,
    overlay_offset_dp: int = 0,
    uc_auth_bypass: bool = False,
) -> None:
    """Verify all literal and Android-version compatibility patches."""
    verify_tree(root, configured_patches(server_url, new_package))
    verify_creator_proxy(root)
    if expect_http_smoke:
        verify_http_smoke(root)
    else:
        path = Path(root) / HTTP_SMOKE_PATH
        text = path.read_text(encoding="utf-8")
        if "local-debug-pay" in text:
            raise ValueError(f"{path}: unexpected HTTP smoke insertion")
    if overlay_offset_dp > 0:
        verify_overlay_offset(root, overlay_offset_dp)
    else:
        overlay_path = Path(root) / OVERLAY_Y_PATH
        if overlay_path.exists() and OVERLAY_MARKER in overlay_path.read_text(encoding="utf-8"):
            raise ValueError(f"{overlay_path}: unexpected overlay offset insertion")
    if uc_auth_bypass:
        verify_uc_auth_bypass(root)
    else:
        uc_path = Path(root) / UC_AUTH_PATH
        if uc_path.exists() and UC_AUTH_METHOD_REF not in uc_path.read_text(encoding="utf-8"):
            raise ValueError(f"{uc_path}: unexpected uc auth bypass insertion")


def main() -> None:
    """Patch the injected smali tree provided on the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("smali_root", type=Path)
    parser.add_argument("--server-url", required=True)
    parser.add_argument("--new-package", default=NEW_PACKAGE)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--http-smoke", action="store_true")
    parser.add_argument("--overlay-offset-dp", type=int, default=0)
    parser.add_argument("--uc-auth-bypass", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify_all(
            args.smali_root,
            args.server_url,
            new_package=args.new_package,
            expect_http_smoke=args.http_smoke,
            overlay_offset_dp=args.overlay_offset_dp,
            uc_auth_bypass=args.uc_auth_bypass,
        )
        print("smali-verify-ok")
    else:
        patch_all(
            args.smali_root,
            args.server_url,
            new_package=args.new_package,
            enable_http_smoke=args.http_smoke,
            overlay_offset_dp=args.overlay_offset_dp,
            uc_auth_bypass=args.uc_auth_bypass,
        )
        print("smali-patch-ok")


if __name__ == "__main__":
    main()
