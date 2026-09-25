"""
picokey-android - PicoKey (Pico HSM / Pico FIDO / Pico OpenPGP) manager for Android.

Pure Python layers of pypicokey (AGPL-3.0, (c) Pol Henarejos) + an Android USB
Host transport written on top of pyjnius, packaged as an APK with Kivy/Buildozer.
"""

__version__ = "0.1.0"

try:
    from .pk import __version__ as PK_VERSION
except Exception:                                  # pragma: no cover
    PK_VERSION = "unknown"

__all__ = ["__version__", "PK_VERSION"]
