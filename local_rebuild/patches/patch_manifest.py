from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ANDROID_NS = "http://schemas.android.com/apk/res/android"
ANDROID = "{" + ANDROID_NS + "}"
OLD_PACKAGE = "com.alibaba.android.rimet"
NEW_PACKAGE = "com.alibaba.android.rimet.localtest"


def local_name(tag: str) -> str:
    """Return an XML element's local name without its namespace."""
    return tag.rsplit("}", 1)[-1]


def replace_prefix(value: str, new_package: str = NEW_PACKAGE) -> str:
    """Replace the application-owned package prefix without touching class-like peers."""
    if value == OLD_PACKAGE or value.startswith(OLD_PACKAGE + "."):
        return new_package + value[len(OLD_PACKAGE) :]
    return value


def replace_authorities(value: str, new_package: str = NEW_PACKAGE) -> str:
    """Rename application-owned tokens in a semicolon-separated authority list."""
    return ";".join(replace_prefix(part.strip(), new_package) for part in value.split(";"))


def patch_manifest(
    path: str | Path,
    new_package: str = NEW_PACKAGE,
    app_label: str | None = None,
) -> dict[str, int]:
    """Rename collision-prone manifest identities while preserving component classes."""
    manifest_path = Path(path)
    ET.register_namespace("android", ANDROID_NS)
    tree = ET.parse(manifest_path)
    root = tree.getroot()
    if root.get("package") != OLD_PACKAGE:
        raise ValueError(f"unexpected manifest package: {root.get('package')}")

    permission_map: dict[str, str] = {}
    for element in root.iter():
        if local_name(element.tag) != "permission":
            continue
        name = element.get(ANDROID + "name", "")
        renamed = replace_prefix(name, new_package)
        if renamed != name:
            permission_map[name] = renamed

    stats = {
        "package": 1,
        "permissions": 0,
        "permission_references": 0,
        "authorities": 0,
        "task_affinities": 0,
        "app_label": 0,
    }
    root.set("package", new_package)

    for element in root.iter():
        tag = local_name(element.tag)
        name_key = ANDROID + "name"
        name = element.get(name_key)
        if tag == "application" and app_label is not None:
            element.set(ANDROID + "label", app_label)
            stats["app_label"] = 1
        elif tag == "permission" and name in permission_map:
            element.set(name_key, permission_map[name])
            stats["permissions"] += 1
        elif tag.startswith("uses-permission") and name in permission_map:
            element.set(name_key, permission_map[name])
            stats["permission_references"] += 1

        for attribute in ("permission", "readPermission", "writePermission"):
            key = ANDROID + attribute
            value = element.get(key)
            if value in permission_map:
                element.set(key, permission_map[value])
                stats["permission_references"] += 1

        if tag == "provider":
            authorities_key = ANDROID + "authorities"
            authorities = element.get(authorities_key)
            if authorities:
                renamed = replace_authorities(authorities, new_package)
                if renamed != authorities:
                    element.set(authorities_key, renamed)
                    stats["authorities"] += 1

        affinity_key = ANDROID + "taskAffinity"
        affinity = element.get(affinity_key)
        if affinity:
            renamed = replace_prefix(affinity, new_package)
            if renamed != affinity:
                element.set(affinity_key, renamed)
                stats["task_affinities"] += 1

    tree.write(manifest_path, encoding="utf-8", xml_declaration=True)
    return stats


def main() -> None:
    """Patch the manifest path supplied on the command line and print change counts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--new-package", default=NEW_PACKAGE)
    parser.add_argument("--app-label", default=None)
    args = parser.parse_args()
    print(
        json.dumps(
            patch_manifest(args.manifest, new_package=args.new_package, app_label=args.app_label),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
