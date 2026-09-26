# PicoKey Manager for Android

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Platform](https://img.shields.io/badge/Platform-Android%208.0%2B-green.svg)](https://www.android.com/)
[![Hardware testing](https://img.shields.io/badge/Hardware%20testing-none%20yet-critical.svg)](#verification-status)
[![Authored by](https://img.shields.io/badge/code%20by-AI-8A2BE2.svg)](#ai-generated-code)

[简体中文](README.md) | English

An Android app that talks to **PicoKey** devices (Pico HSM / Pico FIDO / Pico
OpenPGP) over a USB OTG cable. Plug the key into your phone and you can read
device information, edit the PHY configuration (USB VID/PID, LED pin and
brightness, enabled USB interfaces), blink the LED, reboot the device, or drop
it into flashing mode to load new firmware.

Supported chips: **RP2040, RP2350, ESP32-S2, ESP32-S3** — see
[Supported boards](#supported-boards).

**Download**: a prebuilt APK is on the [Releases](../../releases) page — grab the
latest one. Older versions stay on the same page so you can roll back; see
[CHANGELOG.md](CHANGELOG.md) for what changed in each.

---

## AI-generated code

**The code in this repository was written by AI and is not the work of the
upstream PicoKey authors.** If something misbehaves, suspect this app first —
not your board and not the firmware.

---

## Verification status

The protocol layer has automated self-test coverage, but **none of this code has
ever run against a real PicoKey**:

- Self-tests and simulated links all pass, but they exercise a **mock device**,
  not real hardware responses.
- USB permission prompts, OTG power delivery and vendor-specific HID interface
  handling are all untested on real phones.
- The actual effect of writing PHY config has never been verified.

**So read first, confirm the values, and only then consider writing.**

---

## Supported boards

PicoKeys firmware runs on four chips. The protocol layer is identical across
them; they differ in **how you flash them, how you enter flashing mode, and the
security features**.

| Chip | Typical boards | Flashing mechanism | Secure Boot / Lock |
| --- | --- | --- | --- |
| **RP2040** | Raspberry Pi Pico / Pico W | UF2 (BOOTSEL turns it into a drive) | ❌ none |
| **RP2350** | Pico 2, Waveshare RP2350-One/Zero/Tiny | UF2 (BOOTSEL turns it into a drive) | ✅ full |
| **ESP32-S2** | ESP32-S2 dev boards | esptool / DFU | ⚠️ uncertain |
| **ESP32-S3** | ESP32-S3 SuperMini, DevKitC | esptool / DFU | ⚠️ uncertain |

### RP2040 and RP2350 are not equally secure

- The RP2350 has an OTP region holding the master key that encrypts every stored
  key; with Secure Boot / Secure Lock it resists having the flash read out.
- **The RP2040 has none of this.** Its flash can be read directly — lose the
  board and the private keys on it are gone.

If security is the point, use an RP2350 or an ESP32-S3, not an RP2040.

### Two ESP32 quirks

**The device name changes in download mode.** There the board reports itself as
**"USB JTAG/serial debug unit"**, which is not PicoKey's CCID interface and will
not answer any command. If you see that name in the log, the board is stuck in
download mode — **unplug it, press nothing, plug it back in**.

**Secure Boot support is uncertain.** Upstream claims ESP32-S3 supports it; the
community fork (LibreKeys) marks it `No (// TODO)`. The two disagree. Press
**Read secure boot status** first, and if it comes back empty or nonsensical,
**do not force a write** — blown OTP fuses are physically irreversible.

### Factory VID/PID: you may not need to configure anything

Since January 2026 firmware ships with Raspberry Pi's officially assigned USB IDs:

| Firmware | VID:PID |
| --- | --- |
| Pico HSM | `2E8A:10FD` |
| Pico FIDO | `2E8A:10FE` |
| Pico OpenPGP | `2E8A:10FF` |

Older firmware used the placeholder `FEFF:FCFD`; that is the case where you do
have to change it. **If your goal is simply "a working FIDO2 key" and the VID/PID
is already one of the above, there is nothing to configure.** Changing it is
mainly about impersonating a YubiKey (for certain sites, or so Yubico
Authenticator can manage the device).

---

## Features

- **Device scan** — lists every usable channel:
  - `CCID` — full feature set: device info, PHY, secure boot, reboot
  - `rescue` (vendor `0xFF`) — fallback when the firmware is not up
  - `FIDO HID` — WINK, `authenticatorGetInfo`
- **PHY read/write** — USB VID/PID, product name, LED GPIO and brightness, USB
  interface switches, enabled curves
- **Secure boot** — read status, set the boot key slot, permanent lock
- **Device information** — platform, product, firmware version, flash usage
- **Maintenance** — reboot, enter flashing mode, WINK
- **Firmware flashing** — see [Flashing firmware](#flashing-firmware)
- **Bilingual UI** — 简体中文 / English switchable at the top; the choice is remembered
- **Protocol self-test** — runs the stack against a fake USB pipe, no hardware needed

**One-click firmware switching is not implemented**: the desktop app bundles the
firmware images, and this project has neither those files nor the right to
redistribute them. Enter flashing mode and write the image yourself.

---

## Usage

1. Connect the PicoKey with an **OTG adapter**. **Press no buttons** — holding
   BOOT/BOOTSEL while plugging in puts the board into flashing mode, where it is
   not a PicoKey and the app cannot talk to it.
2. Open the app → **Scan USB devices**. Every available channel appears.
3. Tap one to connect. Android shows a USB authorization dialog — **you must
   allow it** (asked only once; if denied, re-enable it in system settings).
4. On the device screen: refresh info / read PHY / write PHY / WINK / enter
   flashing mode.

If the device is not detected, run **protocol self-test** first — it needs no
hardware. All green means the app is fine and the problem is the cable, the power
supply, or the OTG adapter.

### Recommended order for a first run

1. **Read only, do not write** — if you can read device info, the link works
2. When editing VID/PID, leave other fields blank: they inherit the device's
   current values, so board-specific settings like LED GPIO are not wiped
3. **Enable at least P-256** among the curves (ES256, the most widely compatible
   WebAuthn default) and **leave secp256k1 off** — upstream warns some older
   Android devices do not support it and the device becomes undetectable
4. **Secure boot goes last**, and only when: passkeys are registered and proven in
   daily use, a backup exists, you are on stock upstream firmware, and you accept
   that it is irreversible

---

## Flashing firmware

The app has a **Flash firmware** page (button at the bottom of the scan screen)
covering two mechanically unrelated paths:

| Board | Underlying mechanism | What this app does |
| --- | --- | --- |
| RP2040 / RP2350 | BOOTSEL exposes the flash as a drive; copying a `.uf2` onto it is the whole job | Hands the UF2 to the system file manager, you save it to the `RPI-RP2` / `RP2350` drive |
| ESP32-S2 / S3 | esptool's ROM serial protocol over USB Serial/JTAG — no UF2 bootloader | Implements that protocol directly; no external tool needed |

Firmware can come from a local file or an https URL. Once loaded the app
identifies the format (UF2 / ESP image / ZIP / gzip / a web page fetched by
mistake) and shows the size and target chip.

⚠️ **Neither flashing path has been verified on real hardware.** On your first
run, identify the file without flashing and read the log at each step.

---

## Known limitations

- Requires Android 8.0 (API 26) or newer, a device with USB host support, and an
  OTG adapter.
- No hot-plug monitoring. After unplugging, go back to the scan screen and
  reconnect.
- Secure channel / DKEK features are unavailable (the crypto library they need is
  not bundled); everything else works.
- **The RP2040 has no OTP protection** — its flash can be read directly. Use an
  RP2350 or ESP32-S3 if you need to resist physical extraction.
- The three firmwares (HSM / FIDO / OpenPGP) **cannot coexist**; switching
  requires flashing Pico Nuke to wipe first. Dedicate one board per purpose
  rather than switching back and forth.

---

## Troubleshooting

- **Device found but connection fails** — most likely the USB permission dialog
  was denied. Android asks only once; re-enable it in system settings, or
  reinstall the app.
- **"USB JTAG/serial debug unit" in the log (ESP32)** — the board is in download
  mode, not running PicoKey. Unplug, press nothing, plug back in.
- **Secure boot reads back empty on an ESP32** — the feature is probably not
  implemented on that board. Do not force a write; OTP fuses are irreversible.

---

## License

Upstream `pypicokey` is AGPL-3.0-or-later, and the files under `picokeyapp/pk/`
carry the same license (see `LICENSE`); the Android port and UI are released
under AGPL-3.0-or-later as well.

The bundled font `assets/fonts/NotoSansSC-Regular-subset.ttf` comes from
[Noto Sans SC](https://fonts.google.com/noto/specs/NotoSansSC) and is licensed
under the SIL Open Font License 1.1 (embedding and redistribution allowed), which
is separate from this project's AGPL terms.
