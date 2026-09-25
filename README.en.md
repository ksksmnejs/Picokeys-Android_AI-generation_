# PicoKey Manager for Android

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/Platform-Android%208.0%2B-green.svg)](https://www.android.com/)
[![Built with](https://img.shields.io/badge/Built%20with-Kivy%20%2F%20Buildozer-orange.svg)](https://kivy.org/)
[![Hardware testing](https://img.shields.io/badge/Hardware%20testing-none%20yet-critical.svg)](#project-status)
[![Authored by](https://img.shields.io/badge/Code%20authored%20by-AI-8A2BE2.svg)](#ai-generated-code)

[简体中文](README.md) | English

An Android app that talks to **PicoKey** devices (Pico HSM / Pico FIDO / Pico OpenPGP)
over a USB OTG cable. It is a port of
[pypicokey](https://github.com/IsayIsee/pypicokey), a desktop Python library,
to Android — packaged as an installable APK.

Plug the key into your phone and you can read device information, edit the PHY
configuration (USB VID/PID, LED pin and brightness, enabled USB interfaces),
blink the LED, reboot the device, or reboot it into BOOTSEL mode to drag in new
firmware.

**Download**: a prebuilt APK is published on the
[Releases](../../releases) page of this repository — grab the latest one and
install it.

---

## AI-generated code

**The code in this repository was written by an AI assistant, not by the
upstream PicoKey author.** Review it before you trust it. Two things follow
from that:

- The protocol layer is verified by automated self-tests, but **nothing has
  been run against a real PicoKey** (see [Project status](#project-status)).
- The Android port (`usbhost.py`, `ccid.py`, `ctap.py`, `cbor_mini.py`,
  `detect.py`, `main.py`) is new code written for this project; any bug in it
  is this project's, not upstream's.

If something misbehaves, treat the app as the suspect first.

---

## Why this could not just be packaged as-is

`pypicokey` reaches the device through two channels that do not exist on
Android:

| Desktop dependency | Situation on Android | What this project does |
| --- | --- | --- |
| `pyscard` (PC/SC, CCID smartcard channel) | No `pcscd`, no PC/SC middleware | Calls the Android USB Host API through pyjnius and sends CCID frames itself |
| `pyusb` + `libusb` (rescue channel) | Apps have no raw USB access | Same CCID framing, on the vendor-specific (`0xFF`) interface |

The device protocol itself — CCID framing, APDUs, the PHY TLV block, CTAPHID —
is pure Python and was carried over unchanged. Only the byte pipe underneath
was replaced. Both the CCID and the FIDO HID channel are implemented and
listed automatically on scan.

## Features

- **Device scan** — enumerates USB devices and shows every usable channel:
  - `CCID` — full feature set: device info, PHY, secure boot, reboot
  - `rescue` (vendor `0xFF`) — fallback when the firmware is not up or PC/SC is unusable
  - `FIDO HID` — WINK, `authenticatorGetInfo`
- **Device information** — platform (RP2040/RP2350/ESP32), product, firmware version, flash usage
- **PHY configuration** — read and write USB VID/PID, LED GPIO, LED brightness, enabled USB interfaces
- **WINK** — blink the LED, the fastest "is it alive?" check (FIDO channel)
- **Reboot / reboot to BOOTSEL** — enter UF2 mode to load firmware
- **Built-in protocol self-test** — runs the protocol stack against a fake USB pipe, no hardware required
- **Bilingual UI** — 简体中文 / English switchable from the top-right spinner; the choice is remembered

## Usage

1. Connect the PicoKey with an **OTG adapter**.
2. Open the app → **Scan USB devices**. Every available channel appears in the list.
3. Tap one to connect. Android shows a USB authorization dialog — **you must
   allow it** (it is asked only once; if you deny it, re-enable it in system settings).
4. From the device screen:
   - **Refresh** — platform, product, version, flash usage
   - **Read PHY** — fills the input fields with the current configuration
   - **Write PHY** — applies the changes; the device reboots
   - **WINK** — blinks the LED (FIDO channel only)
   - **Reboot to BOOTSEL** — UF2 mode

If the device is not detected, run **protocol self-test** first: it needs no
hardware. If it is all green, the app is fine and the problem is the cable,
the power supply, or the OTG adapter.

## Project layout

```
main.py                     Kivy UI (scan / device / log screens); USB work runs in threads
picokeyapp/
  i18n.py                   string tables and the t() lookup
  fonts.py                  CJK font registration (replaces Kivy's default Roboto)
  usbhost.py                Android USB Host API: enumeration, permission, claim, bulk IN/OUT
  ccid.py                   CCID transport (feeds upstream's ICCD framing)
  ctap.py                   CTAPHID transport (INIT / WINK / CBOR)
  cbor_mini.py              dependency-free CBOR codec (only for authenticatorGetInfo)
  detect.py                 scans devices, identifies ccid / rescue / fido channels
  selftest.py               protocol self-test that needs no hardware
  pk/                       pure-Python layers ported from upstream (pyscard/pyusb removed)
assets/fonts/               bundled CJK font (Noto Sans SC subset, OFL)
src/android/                AndroidManifest snippet injected at build time
buildozer.spec              Buildozer packaging configuration
.github/workflows/          GitHub Actions APK build
tools/fake_android_check.py integration check driven by a fake jnius
```

## Project status

Verified in development, **without hardware**:

- `python3 -m picokeyapp.selftest` — CCID framing, APDU round-trips, PHY TLV
  parsing, multi-packet reassembly, CTAPHID handshake and CBOR decoding all
  match upstream behaviour.
- `python3 tools/fake_android_check.py` — drives the whole chain
  (enumerate → permission → claim → transfer → connect on all three channels)
  against a fake Android USB Host API.
- The Kivy UI starts, switches screens and handles error paths in a headless run.

**Not verified** — needs a real device:

- USB permission dialog behaviour, OTG power delivery, vendor-specific HID handling.
- Responses of a real PicoKey (the tests use simulated devices).
- The actual effect of a PHY write. **Read before you write** the first time.

## UI language and the CJK font

The UI speaks **简体中文** and **English**; pick one from the spinner at the
top of the scan screen and the choice is stored in `ui_settings.json`.
Switching rebuilds the widget tree and does not drop an active connection.

Chinese used to render as tofu boxes (▯) on Android: Kivy's default font,
Roboto, has no CJK glyphs, and Kivy does not fall back to the system CJK font.
The fix is to ship a font with the APK and register it before any widget is
drawn (`picokeyapp/fonts.py`). The font is **Noto Sans SC** (SIL Open Font
License 1.1, which permits embedding), subsetted to ASCII + GB2312 so it costs
about 2 MB instead of the full 10 MB.

`source.include_exts` in `buildozer.spec` must contain `ttf`, otherwise the
font never reaches the APK and Chinese turns back into boxes.

## Known limitations

- `cryptography` and `pycvc` are deliberately not bundled — modern
  `cryptography` needs a Rust toolchain to cross-compile and tends to break
  p4a builds. Secure channel / DKEK features are therefore unavailable;
  everything else works.
- No hot-plug monitoring. After unplugging, go back to the scan screen and
  reconnect.
- Android 8.0+ (API 26) with USB host support is required, plus an OTG adapter.

## Troubleshooting

- **Build fails with `unrecognized arguments: --feature ...`** — an old
  `buildozer.spec` that still sets `android.features`. Current
  python-for-android dropped that argument; the declaration is injected
  through `android.extra_manifest_xml` instead.
- **Build hangs at "Installing/updating SDK platform tools"** — `sdkmanager`
  waiting for a `y` it can never get in CI. `android.accept_sdk_license = True`
  plus the `yes |` prefix on the build command covers it.
- **Never pre-create `~/.buildozer/android/platform/android-sdk/`** —
  buildozer decides whether to download the SDK by checking whether that path
  exists, and a directory counts. Pre-creating it makes buildozer skip the
  download and then fail with "sdkmanager is not installed".
- **Gradle complains about the JDK** — API 35 needs JDK 17; the workflow
  forces it with `actions/setup-java`.
- **Writing PHY config** changes device configuration and reboots the key.
  Read first, write only when you are sure of the values.

## License

Upstream `pypicokey` is AGPL-3.0-or-later; the files under `picokeyapp/pk/`
keep that license (see `LICENSE`). The Android port and UI are released under
the same terms.

The bundled font `assets/fonts/NotoSansSC-Regular-subset.ttf` comes from
[Noto Sans SC](https://fonts.google.com/noto/specs/NotoSansSC) and is licensed
under the SIL Open Font License 1.1 (embedding and redistribution allowed);
it is not covered by this project's AGPL licence.
