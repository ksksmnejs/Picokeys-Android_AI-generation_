"""
CJK font registration.

The problem
-----------
Kivy ships Roboto as its default font and Roboto has no CJK glyphs, so every
Chinese label rendered as a tofu box (▯) even after the strings were correct.
Android does have a system CJK font, but Kivy does not look at it, so the font
has to be bundled with the APK and registered before any widget is created.

The font
--------
assets/fonts/NotoSansSC-Regular-subset.ttf - Noto Sans SC (SIL Open Font
License 1.1, which explicitly permits embedding), subsetted down to ASCII +
the GB2312 character set so it costs ~2 MB instead of ~10 MB.

Two names are registered on purpose:
  * 'AppFont' - used explicitly by the KV rules below
  * 'Roboto'  - overwritten so that any widget that still falls back to the
                Kivy default (third-party widgets, popups) also renders CJK
"""

from __future__ import annotations

import os

FONT_NAME = "AppFont"
_REL_PATH = os.path.join("assets", "fonts", "NotoSansSC-Regular-subset.ttf")

_registered = False


def _locate() -> str | None:
    """Find the bundled font both on the desktop and inside the APK.

    Inside a p4a APK the app files live under
    /data/data/<pkg>/files/app, which is what __file__ resolves to; the
    resource_find() fallback covers the case where Kivy's resource paths
    differ from that.
    """
    try:
        here = os.path.dirname(os.path.abspath(__file__))        # .../picokeyapp
        root = os.path.dirname(here)                             # project root
        candidate = os.path.join(root, _REL_PATH)
        if os.path.exists(candidate):
            return candidate
    except Exception:
        pass

    try:
        from kivy.resources import resource_find

        found = resource_find(_REL_PATH) or resource_find(os.path.basename(_REL_PATH))
        if found:
            return found
    except Exception:
        pass

    return None


def register(force: bool = False) -> bool:
    """Register the CJK font. Safe to call more than once."""
    global _registered
    if _registered and not force:
        return True

    path = _locate()
    if not path:
        return False

    from kivy.core.text import LabelBase

    try:
        LabelBase.register(FONT_NAME, fn_regular=path, fn_bold=path,
                           fn_italic=path, fn_bolditalic=path)
    except Exception:
        return False

    try:
        # Overwrite Kivy's default so widgets that never set font_name still
        # render Chinese instead of tofu boxes.
        LabelBase.register("Roboto", fn_regular=path, fn_bold=path,
                           fn_italic=path, fn_bolditalic=path)
    except Exception:
        pass

    _registered = True
    return True


def is_registered() -> bool:
    return _registered


def path() -> str | None:
    return _locate()
