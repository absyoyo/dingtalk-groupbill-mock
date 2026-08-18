import xml.etree.ElementTree as ET

import pytest

from local_rebuild.patches.patch_manifest import ANDROID, NEW_PACKAGE, OLD_PACKAGE
from local_rebuild.patches.verify_manifest import verify_manifest


def write_manifest(path, *, application_name="com.alibaba.android.rimet.LauncherApplication"):
    manifest = f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{NEW_PACKAGE}">
  <permission android:name="{NEW_PACKAGE}.permission.IPC" />
  <uses-permission android:name="{NEW_PACKAGE}.permission.IPC" />
  <application android:name="{application_name}">
    <activity android:name="com.alibaba.android.rimet.biz.LaunchHomeActivity"
      android:taskAffinity="{NEW_PACKAGE}.task" />
    <service android:name="example.Service" android:permission="{NEW_PACKAGE}.permission.IPC" />
    <provider android:name="example.Provider"
      android:authorities="{NEW_PACKAGE}.provider"
      android:readPermission="{NEW_PACKAGE}.permission.IPC" />
  </application>
</manifest>
'''
    path.write_text(manifest, encoding="utf-8")


def test_verify_manifest_accepts_localtest_identity(tmp_path):
    path = tmp_path / "AndroidManifest.xml"
    write_manifest(path)

    verify_manifest(path)


def test_verify_manifest_rejects_unrenamed_authority(tmp_path):
    path = tmp_path / "AndroidManifest.xml"
    write_manifest(path)
    tree = ET.parse(path)
    provider = next(element for element in tree.getroot().iter() if element.tag == "provider")
    provider.set(ANDROID + "authorities", OLD_PACKAGE + ".provider")
    tree.write(path, encoding="utf-8", xml_declaration=True)

    with pytest.raises(ValueError, match="unrenamed provider authority"):
        verify_manifest(path)


def test_verify_manifest_rejects_modified_launcher_class(tmp_path):
    path = tmp_path / "AndroidManifest.xml"
    write_manifest(path, application_name=NEW_PACKAGE + ".LauncherApplication")

    with pytest.raises(ValueError, match="LauncherApplication class name was modified"):
        verify_manifest(path)
