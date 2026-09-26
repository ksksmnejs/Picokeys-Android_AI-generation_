# Changelog

Release notes (the body of the Releases page) are **generated from this file**
by GitHub Actions. Write them here; there is no need to touch the workflow.

Format: one second-level heading per version, and the heading must contain the
version number (with or without a `v` prefix, with or without a date). The
workflow matches it against `version` in `buildozer.spec`.

```markdown
## [v0.3.0] - 2026-10-01

### Added
- something

### Fixed
- something
```

---

## [v0.2.0] - 2026-09-26

### Added

- **Flash firmware page** - UF2 sniffing (RP2040/RP2350) plus the ESP32 ROM
  serial download protocol; firmware can come from a local file or an https
  URL, and the format and target chip are detected on load
- Docs now cover the differences between RP2040 / RP2350 / ESP32-S2 / S3
- Added `CHANGELOG.md`; release notes are now generated from it
- Version can be advanced automatically: add a new CHANGELOG section and
  `buildozer.spec` is updated for you

### Fixed

- Status bar covering the top row (the real system status-bar height is now
  read and applied as a top inset)
- Long English button labels being clipped (button height now follows the
  wrapped text height)
- Crash when tapping **Scan** on the firmware page (an exception in the success
  callback now shows an error instead of killing the app)

### Changed

- Firmware page restructured into "1. Pick the board / 2. Pick the firmware /
  3. Write"
- Removed the concrete button gestures for entering flashing mode - they differ
  per board, so hardcoding them misleads. The UI now just says to consult the
  board's own documentation
- Publishing now refuses to overwrite an existing tag by default, preserving
  earlier versions

## [v0.1.0] - 2026-09-25

First release.

- USB OTG connection, three-channel scan (CCID / rescue / FIDO HID)
- Device information, PHY configuration read/write, secure boot
- Reboot and flashing mode, WINK
- Protocol self-test that needs no hardware
- Bilingual UI with a bundled CJK font
