# Dynamic Observations

## Environment

- ADB and Frida connectivity succeeded on an authorized arm64 Android 12 device.
- The device had an existing DingTalk installation, but it was version `8.3.30`; the analyzed APK is `8.3.41` and the files are different.
- No emulator or secondary Android user was available for side-by-side installation.

## Safe Validation Performed

- The existing installation was not overwritten or resigned.
- Frida server `17.8.0` was started temporarily.
- `frida-trace` attached to the existing DingTalk process and resolved `com.alibaba.surgeon.instrument.InstrumentAPI.support` as a traceable Java method.
- No calls were observed during the short idle/relaunch window, so the trace does not prove target-version behavior.
- No business arguments, account values, message contents, payment data, or network payloads were collected.

## Cleanup

- The temporary Frida server process was stopped.
- The DingTalk process launched for validation was force-stopped.

## Limitation

Target-version dynamic verification requires an isolated device/emulator where package `com.alibaba.android.rimet` can be installed without replacing an existing installation. Static evidence remains authoritative for this report.
