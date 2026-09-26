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
Supported chips: **RP2040, RP2350, ESP32-S2 and ESP32-S3**
(see [Supported boards](#supported-boards)).

Plug the key into your phone and you can read device information, edit the PHY
configuration (USB VID/PID, LED pin and brightness, enabled USB interfaces),
blink the LED, reboot the device, or drop it into flashing mode to load new
firmware.

**Download**: a prebuilt APK is published on the
[Releases](../../releases) page of this repository — grab the latest one and
install it.

Every run of the **Build Android APK** workflow publishes the freshly built APK
to Releases automatically, with **bilingual (zh/en) release notes** carrying the
version, the commit, the install steps and the caveats. If a release for that
tag already exists, the workflow replaces its APK and refreshes the notes
instead of creating a duplicate.

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

## Supported boards

PicoKeys firmware runs on four chips. The protocol layer is identical across
all of them; the differences are entirely in **how you flash it, the gesture
that enters flashing mode, and the security features** — which is the only
reason this app has to treat boards differently at all.

| Chip | Typical boards | Flashing mechanism | Enter flashing mode | Secure Boot / Lock |
| --- | --- | --- | --- | --- |
| **RP2040** | Raspberry Pi Pico / Pico W | UF2 (BOOTSEL turns it into a drive) | Hold BOOTSEL while plugging in | ❌ no hardware protection |
| **RP2350** | Pico 2, Waveshare RP2350-One/Zero/Tiny | UF2 (BOOTSEL turns it into a drive) | Hold BOOTSEL while plugging in | ✅ fully supported |
| **ESP32-S2** | ESP32-S2 dev boards | esptool / DFU | Hold BOOT → tap RESET → release RESET → release BOOT | ⚠️ see below |
| **ESP32-S3** | ESP32-S3 SuperMini, DevKitC | esptool / DFU | Same as above | ⚠️ see below |

### RP2040 vs RP2350 (it is not just clock speed)

Both take UF2, but their **security models are completely different**:

- The RP2350 has an OTP (one-time-programmable) region that can hold the master
  key (MKEK) encrypting every stored key. Together with Secure Boot / Secure
  Lock it resists having the flash read out.
- **The RP2040 has none of this.** Its flash contents can be read directly; if
  the board is lost, the private keys on it are exposed.

So if security is the point, use an RP2350 or an ESP32-S3, not an RP2040.

### Two ESP32-S2/S3 quirks

**1. Two USB controllers share one PHY**

The ESP32-S3 has USB Serial/JTAG (fixed function: flashing and debugging) and
USB-OTG (programmable, TinyUSB), but they **share a single internal USB PHY** —
only one can own the native USB connector at a time. The running firmware uses
one; download mode uses the other.

**2. The device name changes in download mode**

In download mode the board reports itself as **"USB JTAG/serial debug unit"**
with a different VID/PID. That is not PicoKey's CCID interface, and **sending
CCID to it gets no answer at all**.

If that name shows up in the app log, the board is stuck in download mode —
**unplug it, press nothing, and plug it back in** so the firmware starts
normally. This app pops up a warning when it sees that name.

### Secure Boot on ESP32

The upstream README claims ESP32-S3 supports Secure Boot and Secure Lock, but
the community fork (LibreKeys) marks both as `No (// TODO)` for ESP32-S2/S3
and lists full support only for the RP2350. The two sources disagree and
**this project cannot settle it for you**.

Practical advice: press **Read secure boot status** first. If it comes back
empty or nonsensical, the feature is not implemented on that board — **do not
force a write**. Blown OTP fuses are physically irreversible.

### Factory VID/PID

Since January 2026 firmware ships with Raspberry Pi's officially assigned USB
IDs, so commissioning is no longer needed just to be recognised:

| Firmware | VID:PID |
| --- | --- |
| Pico HSM | `2E8A:10FD` |
| Pico FIDO | `2E8A:10FE` |
| Pico OpenPGP | `2E8A:10FF` |

Older firmware used the placeholder `FEFF:FCFD`; that is the case where you do
have to change it. **If your goal is simply "a working FIDO2 key" and the
VID/PID is already one of the above, there is nothing to configure** — changing
it is mainly about impersonating a YubiKey (for certain sites, or for Yubico
Authenticator to manage it).


## Features

- **Device scan** — enumerates USB devices and shows every usable channel:
  - `CCID` — full feature set: device info, PHY, secure boot, reboot
  - `rescue` (vendor `0xFF`) — fallback when the firmware is not up or PC/SC is unusable
  - `FIDO HID` — WINK, `authenticatorGetInfo`
- **Device information** — platform (RP2040/RP2350/ESP32), product, firmware version, flash usage
- **PHY configuration** — read and write USB VID/PID, LED GPIO, LED brightness, enabled USB interfaces
- **WINK** — blink the LED, the fastest "is it alive?" check (FIDO channel)
- **Reboot / enter flashing mode** — BOOTSEL on RP2040/RP2350, download mode on ESP32
- **Built-in protocol self-test** — runs the protocol stack against a fake USB pipe, no hardware required
- **Bilingual UI** — 简体中文 / English switchable from the top-right spinner; the choice is remembered

## Usage

1. Connect the PicoKey with an **OTG adapter**. **Press no buttons** — holding
   BOOT/BOOTSEL while plugging in puts the board into flashing mode, where it is
   not a PicoKey and the app cannot talk to it (an ESP32 then shows up as
   "USB JTAG/serial debug unit").
2. Open the app → **Scan USB devices**. Every available channel appears in the list.
3. Tap one to connect. Android shows a USB authorization dialog — **you must
   allow it** (it is asked only once; if you deny it, re-enable it in system settings).
4. From the device screen:
   - **Refresh** — platform, product, version, flash usage
   - **Read PHY** — fills the input fields with the current configuration
   - **Write PHY** — applies the changes; the device reboots
   - **WINK** — blinks the LED (FIDO channel only)
   - **Enter flashing mode** — BOOTSEL on RP2040/RP2350, download mode on ESP32

If the device is not detected, run **protocol self-test** first: it needs no
hardware. If it is all green, the app is fine and the problem is the cable,
the power supply, or the OTG adapter.

### Recommended order for a first run

1. **Read only, do not write** — if you can read device info, the link works
2. When editing VID/PID, leave other fields blank: they inherit the device's
   current values, so board-specific settings like LED GPIO are not wiped
3. **Enable at least P-256** among the curves (ES256, the most widely
   compatible WebAuthn default) plus Ed25519 if you like; **leave secp256k1
   off** — upstream warns some older Android devices do not support it and the
   device becomes undetectable
4. **Secure boot goes last**, and only when: passkeys are registered and proven
   in daily use, a backup exists, you are on stock upstream firmware, and you
   accept that it is irreversible

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
  detect.py                 scans devices, identifies ccid / rescue / fido
  flasher.py                firmware flashing: UF2 sniffing + ESP32 ROM serial protocol channels
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
Switching rebuilds the three screen bodies and does not drop an active
connection.

> **Implementation note**: each screen body is built as an **anonymous root
> widget** rather than a `<Screen>:` class rule. Class rules are registered
> against the class, and re-loading one does not replace it - it *adds*
> another, so an earlier version piled a whole extra set of widgets onto the
> screen on every language switch (3 buttons, then 6, then 9...), which showed
> up as "half Chinese, half English, buttons dead". An anonymous root produces
> an instance and no class rule, so nothing accumulates.

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
- **The RP2040 has no OTP protection** — its flash can be read directly. Use an
  RP2350 or ESP32-S3 if you need to resist physical extraction (and confirm
  Secure Boot actually works on that board first).
- **Secure Boot / Secure Lock on ESP32-S2/S3 are uncertain** — upstream and the
  community fork disagree. This app only exposes read and write: read first,
  and if the read fails, do not write.
- The three firmwares (HSM / FIDO / OpenPGP) **cannot coexist**; switching
  requires flashing Pico Nuke to wipe first. Dedicate one board per purpose
  rather than switching back and forth.

## Flashing firmware

The app has a **Flash firmware** page (button at the bottom of the scan
screen). It covers two **mechanically unrelated** paths:

| Board | Underlying mechanism | What this app does |
| --- | --- | --- |
| RP2040 / RP2350 | BOOTSEL makes the Boot ROM expose the flash as USB mass storage; copying a `.uf2` onto it is the whole job | Hands the UF2 to the system file manager, you save it to the `RPI-RP2` (RP2040) or `RP2350` drive |
| ESP32-S2 / S3 | esptool's ROM serial protocol over USB Serial/JTAG — **there is no UF2 bootloader** | Implements that protocol directly (SLIP framing + FLASH_BEGIN/DATA/END); no external tool needed |

Firmware can come from a local file or an https URL. Once loaded the app
identifies the format (UF2 / ESP image / ZIP / gzip / a web page you fetched by
mistake) and shows the size and target chip.

### Entering flashing mode, per board

**RP2040 / RP2350**: hold **BOOTSEL** → plug in → release. A drive appears on
the phone; save the UF2 there and it flashes automatically. No drivers needed.

**ESP32-S2 / S3**: hold **BOOT** → tap **RESET** → release RESET → release
BOOT. If the order is wrong, or you only held BOOT without tapping RESET, the
chip keeps running the old program. In download mode the device name becomes
"USB JTAG/serial debug unit".

⚠️ **Neither flashing path has been verified on real hardware.**

- An ESP32 failure is **usually recoverable** (the ROM download mode can rescue
  it) — that is its advantage
- The RP2040/RP2350 UF2 path just delegates to the system file manager and is
  reliable on its own
- On your first run, **identify the file without flashing** and read the log at
  each step

Also: making USB-OTG fully own the ESP32-S3's connector requires burning the
`USB_PHY_SEL` eFuse — **permanently irreversible**. This app will not walk you
into that.

## Troubleshooting

- **`Didn't find class "org.jnius.NativeInvocationHandler"`** — a known pyjnius
  trap. It can only resolve Java classes from a thread that carries the Android
  class loader; a plain `threading.Thread` has none, so the JVM reports an empty
  classpath (`DexPathList[[directory "."]]`). That class is the proxy pyjnius
  generates whenever a Python object stands in for a Java interface - which is
  what registering a BroadcastReceiver needs. This project avoids it two ways:
  USB permission is granted by polling `UsbManager.hasPermission()` (no proxy at
  all), and every Java class it will ever touch is preloaded in `App.build()` on
  the UI thread, which puts them in pyjnius' cache.
- **Device is listed but connecting fails** — usually the USB authorization
  dialog was denied. Android asks only once; re-enable it in system settings or
  reinstall the app.

## Troubleshooting (build)

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
