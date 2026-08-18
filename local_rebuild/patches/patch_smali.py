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


@dataclass(frozen=True)
class PatchSpec:
    """Describe one exact literal replacement in one injected smali file."""

    relative_path: Path
    original: str
    replacement: str
    expected_count: int


PATCHES = (
    PatchSpec(
        Path("classes37/com/dingtalk/groupbill/ModuleLoader.smali"),
        OLD_PACKAGE,
        NEW_PACKAGE,
        2,
    ),
    PatchSpec(
        Path("classes37/com/dingtalk/groupbill/HookMain.smali"),
        OLD_PACKAGE,
        NEW_PACKAGE,
        1,
    ),
    PatchSpec(
        Path("classes37/com/dingtalk/groupbill/GroupBillHooks$3.smali"),
        OLD_PACKAGE,
        NEW_PACKAGE,
        1,
    ),
    PatchSpec(
        Path("classes38/com/pineloader/PineLoader.smali"),
        OLD_PACKAGE,
        NEW_PACKAGE,
        1,
    ),
)


def configured_patches(server_url: str) -> tuple[PatchSpec, ...]:
    """Return all exact smali replacements for one normalized backend URL."""
    endpoint_patch = PatchSpec(
        Path("classes36/com/dingtalk/groupbill/net/HttpReporter.smali"),
        OLD_ENDPOINT,
        normalize_server_url(server_url),
        1,
    )
    return (endpoint_patch, *PATCHES)


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
    *,
    enable_http_smoke: bool = False,
) -> None:
    """Apply all literal and Android-version compatibility patches."""
    patch_tree(root, configured_patches(server_url))
    patch_creator_proxy(root)
    if enable_http_smoke:
        patch_http_smoke(root)


def verify_all(
    root: str | Path,
    server_url: str,
    *,
    expect_http_smoke: bool = False,
) -> None:
    """Verify all literal and Android-version compatibility patches."""
    verify_tree(root, configured_patches(server_url))
    verify_creator_proxy(root)
    if expect_http_smoke:
        verify_http_smoke(root)
    else:
        path = Path(root) / HTTP_SMOKE_PATH
        text = path.read_text(encoding="utf-8")
        if "local-debug-pay" in text:
            raise ValueError(f"{path}: unexpected HTTP smoke insertion")


def main() -> None:
    """Patch the injected smali tree provided on the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("smali_root", type=Path)
    parser.add_argument("--server-url", required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--http-smoke", action="store_true")
    args = parser.parse_args()
    if args.verify:
        verify_all(
            args.smali_root,
            args.server_url,
            expect_http_smoke=args.http_smoke,
        )
        print("smali-verify-ok")
    else:
        patch_all(
            args.smali_root,
            args.server_url,
            enable_http_smoke=args.http_smoke,
        )
        print("smali-patch-ok")


if __name__ == "__main__":
    main()
