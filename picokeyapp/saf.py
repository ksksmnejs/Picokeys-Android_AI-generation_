"""Pick a file with the Android system file manager.

Kivy's built-in FileChooser cannot see most of a modern phone's storage.
Since Android 10 scoped storage restricts what an app may enumerate, so the
chooser rooted at /sdcard ends up listing only the handful of directories that
other apps happen to expose (QQ, Quark, Browser, ...) - which is why firmware
files stored elsewhere were simply invisible.

The Storage Access Framework (SAF) is the supported answer: hand an
ACTION_OPEN_DOCUMENT intent to the system, let whatever file manager the user
has browse the real storage, and receive a content:// Uri back. No storage
permission is required and every location the user can reach - internal
storage, SD card, USB OTG drives, cloud providers - works the same way.

This module is imported unconditionally, but every Android entry point is
resolved lazily so the desktop build (and the test suite) still import it fine.
"""

from __future__ import annotations

# Request code is arbitrary but must be stable: it is how we recognise our own
# result coming back in on_activity_result.
REQUEST_PICK_FILE = 0x51F0      # "SF" - arbitrary, just unique within the app


class SafUnavailable(Exception):
    """Raised when SAF cannot be used (not on Android, or no file manager)."""


def is_available() -> bool:
    """True when we are on Android and can build the intent."""
    try:
        from jnius import autoclass                      # noqa: F401
    except Exception:
        return False
    return True


def _intent():
    """Build ACTION_OPEN_DOCUMENT.

    setType("*/*") is deliberate: .uf2 and .bin have no registered MIME type,
    so filtering on one would hide exactly the files we need.
    """
    from jnius import autoclass
    Intent = autoclass("android.content.Intent")
    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("*/*")
    return intent


def open_picker(on_result):
    """Hand the file picker to the system.

    `on_result(uri)` is called with the chosen android.net.Uri, or None when
    the user backed out. Returns immediately - the result arrives later.
    """
    from jnius import autoclass
    from android import activity

    PythonActivity = autoclass("org.kivy.android.PythonActivity")

    def _on_activity_result(request_code, result_code, data):
        if request_code != REQUEST_PICK_FILE:
            return
        # Unbind so a second pick does not stack handlers.
        try:
            activity.unbind(on_activity_result=_on_activity_result)
        except Exception:
            pass
        try:
            if data is None:
                on_result(None)
                return
            on_result(data.getData())
        except Exception:
            on_result(None)

    # Keep a reference: Kivy's activity module stores callbacks in a way that
    # can be collected if the only holder is a local closure.
    open_picker._pending = _on_activity_result
    activity.bind(on_activity_result=_on_activity_result)

    try:
        PythonActivity.mActivity.startActivityForResult(
            _intent(), REQUEST_PICK_FILE)
    except Exception as exc:
        raise SafUnavailable(str(exc)) from exc


def read_uri(uri) -> bytes:
    """Read the whole content of a content:// Uri.

    Uses ContentResolver.openInputStream. Going through the resolver is the
    only correct way - Uri.getPath() is not a filesystem path and opening it
    with Python's open() fails on every modern Android version.
    """
    from jnius import autoclass, jarray

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    resolver = PythonActivity.mActivity.getContentResolver()
    stream = resolver.openInputStream(uri)
    if stream is None:
        raise SafUnavailable("could not open the selected file")

    try:
        ByteArrayOutputStream = autoclass("java.io.ByteArrayOutputStream")
        bos = ByteArrayOutputStream()
        buf = jarray("b")(65536)
        try:
            while True:
                n = stream.read(buf)
                if n is None or n < 0:
                    break
                bos.write(buf, 0, n)
        finally:
            stream.close()
        return bytes(bos.toByteArray())
    finally:
        try:
            bos.close()
        except Exception:
            pass


def display_name(uri) -> str:
    """Best-effort file name for a Uri, for showing back to the user."""
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        OpenableColumns = autoclass("android.provider.OpenableColumns")
        resolver = PythonActivity.mActivity.getContentResolver()
        cursor = resolver.query(uri, None, None, None, None)
        if cursor is None:
            return ""
        try:
            if cursor.moveToFirst():
                idx = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if idx >= 0:
                    return cursor.getString(idx) or ""
        finally:
            cursor.close()
    except Exception:
        pass
    return ""
