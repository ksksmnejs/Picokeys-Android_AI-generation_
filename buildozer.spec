[app]
title = PicoKey Manager
package.name = picokeymanager
package.domain = org.picokey

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,md
source.exclude_dirs = tests,docs,.github,tools,build,bin,.buildozer,__pycache__

version = 0.1.0

# python3 + kivy pull in pyjnius by themselves; cryptography/pycvc are NOT
# listed on purpose (they would need a Rust toolchain for the modern
# cryptography wheels) - the app degrades gracefully without them.
requirements = python3,kivy,pyjnius

orientation = portrait
fullscreen = 0

# ---------------------------------------------------------------- android

# USB host needs no runtime permission, but the feature must be declared or
# Play/other stores treat the app as incompatible with OTG-less devices.
android.features = android.hardware.usb.host
android.permissions =

android.api = 35
android.minapi = 26
# arm64 only: one arch roughly halves the build time and every current phone
# (including the Snapdragon 8+ Gen1 in a OnePlus Ace 2) is arm64-v8a. Add
# armeabi-v7a back here only if you need a 32-bit device.
android.archs = arm64-v8a
android.allow_backup = True

# CI has no terminal for the "do you accept the license?" prompt that
# sdkmanager prints on first run - without this the build dies at
# "Installing/updating SDK platform tools". Automation only; never set it
# locally unless you have actually read and accepted the SDK terms.
android.accept_sdk_license = True

# make `adb logcat | grep python` readable while debugging on the phone
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1

# Uncomment if the default p4a release cannot build your dependencies:
# p4a.branch = develop
