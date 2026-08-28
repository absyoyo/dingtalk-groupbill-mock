from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

from local_rebuild.patches.patch_manifest import (
    ANDROID,
    NEW_PACKAGE,
    OLD_PACKAGE,
    local_name,
)


LAUNCHER_APPLICATION = "com.alibaba.android.rimet.LauncherApplication"
LAUNCHER_ACTIVITY = "com.alibaba.android.rimet.biz.LaunchHomeActivity"


def is_old_identity(value: str, new_package: str = NEW_PACKAGE) -> bool:
    """Return whether a manifest identity still uses the original package prefix."""
    if value == new_package or value.startswith(new_package + "."):
        return False
    return value == OLD_PACKAGE or value.startswith(OLD_PACKAGE + ".")


def verify_manifest(path: str | Path, new_package: str = NEW_PACKAGE) -> None:
    """Verify coexistence identities while preserving original component class names."""
    root = ET.parse(path).getroot()
    if root.get("package") != new_package:
        raise ValueError("rebuilt package identity is incorrect")

    application = next(
        element for element in root.iter() if local_name(element.tag) == "application"
    )
    if application.get(ANDROID + "name") != LAUNCHER_APPLICATION:
        raise ValueError("LauncherApplication class name was modified")

    activity_names = {
        element.get(ANDROID + "name", "")
        for element in root.iter()
        if local_name(element.tag) in {"activity", "activity-alias"}
    }
    if LAUNCHER_ACTIVITY not in activity_names:
        raise ValueError("LaunchHomeActivity component is missing")

    for element in root.iter():
        tag = local_name(element.tag)
        if tag == "permission":
            value = element.get(ANDROID + "name", "")
            if is_old_identity(value, new_package):
                raise ValueError(f"unrenamed app permission: {value}")
        if tag.startswith("uses-permission"):
            value = element.get(ANDROID + "name", "")
            if is_old_identity(value, new_package):
                raise ValueError(f"unrenamed app permission reference: {value}")
        for attribute in ("permission", "readPermission", "writePermission"):
            value = element.get(ANDROID + attribute, "")
            if is_old_identity(value, new_package):
                raise ValueError(f"unrenamed component permission reference: {value}")
        if tag == "provider":
            for authority in element.get(ANDROID + "authorities", "").split(";"):
                if is_old_identity(authority.strip(), new_package):
                    raise ValueError(f"unrenamed provider authority: {authority}")
        affinity = element.get(ANDROID + "taskAffinity", "")
        if is_old_identity(affinity, new_package):
            raise ValueError(f"unrenamed task affinity: {affinity}")


def main() -> None:
    """Verify a decoded rebuilt manifest from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--new-package", default=NEW_PACKAGE)
    args = parser.parse_args()
    verify_manifest(args.manifest, new_package=args.new_package)
    print("manifest-verify-ok")


if __name__ == "__main__":
    main()
