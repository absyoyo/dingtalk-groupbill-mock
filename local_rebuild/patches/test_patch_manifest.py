import xml.etree.ElementTree as ET

import pytest

from local_rebuild.patches.patch_manifest import ANDROID, NEW_PACKAGE, OLD_PACKAGE, patch_manifest


MANIFEST = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{OLD_PACKAGE}">
  <permission android:name="{OLD_PACKAGE}.permission.IPC" android:protectionLevel="signature" />
  <uses-permission android:name="{OLD_PACKAGE}.permission.IPC" />
  <uses-permission-sdk-23 android:name="{OLD_PACKAGE}.permission.IPC" />
  <uses-permission android:name="android.permission.INTERNET" />
  <application android:name="com.alibaba.android.rimet.LauncherApplication">
    <activity android:name="com.alibaba.android.rimet.biz.LaunchHomeActivity"
      android:taskAffinity="{OLD_PACKAGE}.BokuiExternalActivity">
      <intent-filter><action android:name="{OLD_PACKAGE}.SEND" /></intent-filter>
    </activity>
    <service android:name="example.Service" android:permission="{OLD_PACKAGE}.permission.IPC" />
    <provider android:name="example.Provider"
      android:authorities="{OLD_PACKAGE}.provider;external.provider"
      android:readPermission="{OLD_PACKAGE}.permission.IPC"
      android:writePermission="{OLD_PACKAGE}.permission.IPC" />
    <meta-data android:name="class" android:value="com.alibaba.android.rimet.impls.FeatureSwitchInterfaceImpl" />
  </application>
</manifest>
'''


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def test_patch_manifest_changes_collision_prone_identity_values_only(tmp_path):
    path = tmp_path / "AndroidManifest.xml"
    path.write_text(MANIFEST, encoding="utf-8")

    stats = patch_manifest(path)

    root = ET.parse(path).getroot()
    assert root.get("package") == NEW_PACKAGE
    values = {
        (local_name(element.tag), key, value)
        for element in root.iter()
        for key, value in element.attrib.items()
    }
    assert ("permission", ANDROID + "name", NEW_PACKAGE + ".permission.IPC") in values
    assert ("uses-permission", ANDROID + "name", NEW_PACKAGE + ".permission.IPC") in values
    assert ("uses-permission-sdk-23", ANDROID + "name", NEW_PACKAGE + ".permission.IPC") in values
    assert ("service", ANDROID + "permission", NEW_PACKAGE + ".permission.IPC") in values
    assert ("provider", ANDROID + "authorities", NEW_PACKAGE + ".provider;external.provider") in values
    assert ("provider", ANDROID + "readPermission", NEW_PACKAGE + ".permission.IPC") in values
    assert ("provider", ANDROID + "writePermission", NEW_PACKAGE + ".permission.IPC") in values
    assert ("activity", ANDROID + "taskAffinity", NEW_PACKAGE + ".BokuiExternalActivity") in values
    assert ("activity", ANDROID + "name", "com.alibaba.android.rimet.biz.LaunchHomeActivity") in values
    assert ("action", ANDROID + "name", OLD_PACKAGE + ".SEND") in values
    assert ("meta-data", ANDROID + "value", "com.alibaba.android.rimet.impls.FeatureSwitchInterfaceImpl") in values
    assert ("uses-permission", ANDROID + "name", "android.permission.INTERNET") in values
    assert stats == {
        "package": 1,
        "permissions": 1,
        "permission_references": 5,
        "authorities": 1,
        "task_affinities": 1,
    }


def test_patch_manifest_rejects_unexpected_source_package(tmp_path):
    path = tmp_path / "AndroidManifest.xml"
    path.write_text(
        MANIFEST.replace(f'package="{OLD_PACKAGE}"', 'package="other.package"'),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unexpected manifest package"):
        patch_manifest(path)
