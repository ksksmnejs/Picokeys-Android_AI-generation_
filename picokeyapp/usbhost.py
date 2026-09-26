"""
Android USB Host access through pyjnius.

Why this file exists
--------------------
Android gives apps no pcscd and no raw libusb access, so neither `pyscard`
(normally used by pypicokey for the CCID/smartcard channel) nor `pyusb`
(normally used for the "rescue" channel) can work inside an APK. The only
supported way to talk to a USB device from an app is the Android USB Host API
(`android.hardware.usb.*`), which this module wraps behind a tiny,
transport-agnostic API:

    Connection.write(data)  -> int
    Connection.read(n)      -> bytes
    Connection.control_in() -> bytes

Everything above this layer (CCID framing, CTAPHID framing, the PicoKey APDU
command set) is plain Python and stays platform independent.

Notes learned the hard way
--------------------------
* pyjnius copies Python `bytearray` buffers into the JVM and copies them back
  after the call, so a `bytearray` behaves like a real Java byte[] buffer and
  is the only correct way to do IN transfers.
* `claimInterface(intf, True)` is required to detach a kernel driver (the HID
  driver binds FIDO interfaces on most phones).
* Android 13+ (API 33) refuses dynamically registered receivers unless
  RECEIVER_EXPORTED / RECEIVER_NOT_EXPORTED is given.
"""

from __future__ import annotations

import threading
import time

from .i18n import t
from .pk.core.log import get_logger

logger = get_logger("usbhost")

# ----------------------------------------------------------------- constants

USB_DIR_IN = 0x80
USB_DIR_OUT = 0x00

USB_ENDPOINT_XFER_CONTROL = 0
USB_ENDPOINT_XFER_ISOC = 1
USB_ENDPOINT_XFER_BULK = 2
USB_ENDPOINT_XFER_INT = 3

USB_CLASS_HID = 0x03
USB_CLASS_SMARTCARD = 0x0B
USB_CLASS_VENDOR = 0xFF

ACTION_USB_PERMISSION = "org.picokey.android.USB_PERMISSION"

# GET_DESCRIPTOR / HID REPORT descriptor
USB_REQ_GET_DESCRIPTOR = 0x06
HID_REPORT_DESCRIPTOR_TYPE = 0x22


class UsbError(Exception):
    pass


# ------------------------------------------------------------------ jnius glue

_J = {}


def is_android() -> bool:
    if "jnius" not in _J:
        try:
            import jnius  # noqa: F401
            _J["jnius"] = True
        except Exception:
            _J["jnius"] = False
    return _J["jnius"]


def _autoclass(name):
    if not is_android():
        raise UsbError("pyjnius is only available inside the Android APK")
    if name not in _J:
        from jnius import autoclass
        _J[name] = autoclass(name)
    return _J[name]


def activity():
    return _autoclass("org.kivy.android.PythonActivity").mActivity


def usb_manager():
    act = activity()
    ctx = _autoclass("android.content.Context")
    manager = act.getSystemService(ctx.USB_SERVICE)
    return manager


def status_bar_height_dp() -> float:
    """Height of the Android status bar, in Kivy dp.

    Kivy draws from y=0 of the window, so on a notch/punch-hole phone the top
    row of widgets ends up underneath the status bar icons. Reading the
    framework dimension is the reliable way to get the real inset - hardcoding
    a value breaks on the many OEMs that draw a taller bar.

    Returns 0 on desktop or if the lookup fails; the caller just adds it.
    """
    if not is_android():
        return 0.0
    try:
        act = activity()
        res = act.getResources()
        res_id = res.getIdentifier("status_bar_height", "dimen", "android")
        if res_id <= 0:
            return 0.0
        px = res.getDimensionPixelSize(res_id)
        density = res.getDisplayMetrics().density
        if not density:
            return 0.0
        # Kivy dp is defined against a 160dpi baseline, same as Android dp.
        return float(px) / float(density)
    except Exception:
        # A missing/renamed dimension is not worth crashing the UI over.
        return 0.0


# Every Java class this module can possibly touch. Resolving them once, on the
# Android UI thread, is what makes the rest of the module usable from Python
# worker threads - see preload_java_classes().
_PRELOAD_CLASSES = (
    "org.kivy.android.PythonActivity",
    "android.content.Context",
    "android.hardware.usb.UsbManager",
    "android.os.Build",
    "android.content.Intent",
    "android.content.IntentFilter",
    "android.app.PendingIntent",
    # The two classes that matter most for the proxy machinery:
    #   org.jnius.NativeInvocationHandler  - used by PythonJavaClass
    #   org.kivy.android.GenericBroadcastReceiver - used by android.broadcast
    "org.jnius.NativeInvocationHandler",
    "org.kivy.android.GenericBroadcastReceiver",
)


def preload_java_classes(verbose: bool = False) -> list:
    """Resolve every Java class we might use, on the thread that can find them.

    THIS MUST BE CALLED FROM THE ANDROID UI THREAD (i.e. from App.build()).

    Why it exists
    -------------
    pyjnius looks Java classes up through the calling thread's class loader. A
    Python thread started with threading.Thread() has no Android class loader
    attached, so the JVM reports an empty classpath - the error text is
    characteristic:

        java.lang.ClassNotFoundException: Didn't find class
        "org.jnius.NativeInvocationHandler" on path:
        DexPathList[[directory "."], nativeLibraryDirectories=[...]]

    That class is the proxy pyjnius creates whenever a Python object stands in
    for a Java interface (PythonJavaClass), which is exactly what registering a
    BroadcastReceiver needs. Touching the class once on the UI thread puts it
    in pyjnius' cache, and later lookups from worker threads then succeed.

    Returns the list of class names that could not be resolved (non-fatal).
    """
    missing = []
    for name in _PRELOAD_CLASSES:
        try:
            _autoclass(name)
            if verbose:
                logger.debug("preloaded " + name)
        except Exception as e:
            missing.append(name)
            logger.debug("could not preload %s: %s", name, e)
    return missing


# --------------------------------------------------------------- descriptors

class Endpoint:
    def __init__(self, address, direction, type_, max_packet_size, interval, number):
        self.address = address
        self.direction = direction
        self.type = type_
        self.max_packet_size = max_packet_size
        self.interval = interval
        self.number = number

    @property
    def is_in(self):
        return bool(self.address & USB_DIR_IN)

    @property
    def type_name(self):
        return {0: "control", 1: "isoc", 2: "bulk", 3: "interrupt"}.get(self.type, "?")

    def __repr__(self):
        return f"<EP 0x{self.address:02X} {self.type_name} {'IN' if self.is_in else 'OUT'} {self.max_packet_size}B>"


class Interface:
    def __init__(self, index, interface_id, cls, subclass, protocol, endpoints):
        self.index = index
        self.id = interface_id
        self.cls = cls
        self.subclass = subclass
        self.protocol = protocol
        self.endpoints = endpoints

    def find(self, direction_in: bool, types=(USB_ENDPOINT_XFER_BULK, USB_ENDPOINT_XFER_INT)):
        for ep in self.endpoints:
            if ep.is_in == direction_in and ep.type in types:
                return ep
        return None

    @property
    def ep_in(self):
        return self.find(True)

    @property
    def ep_out(self):
        return self.find(False)

    @property
    def class_name(self):
        return {USB_CLASS_HID: "HID", USB_CLASS_SMARTCARD: "CCID/Smartcard",
                USB_CLASS_VENDOR: "Vendor-specific"}.get(self.cls, f"0x{self.cls:02X}")

    def __repr__(self):
        eps = ", ".join(repr(e) for e in self.endpoints)
        return f"<IF#{self.id} {self.class_name} [{eps}]>"


class Device:
    def __init__(self, jdevice, vid, pid, manufacturer, product, serial, interfaces):
        self._jdevice = jdevice
        self.vid = vid
        self.pid = pid
        self.manufacturer = manufacturer or ""
        self.product = product or ""
        self.serial = serial or ""
        self.interfaces = interfaces
        self.device_id = int(jdevice.getDeviceId())

    @property
    def jdevice(self):
        return self._jdevice

    @property
    def label(self):
        bits = [b for b in (self.manufacturer, self.product) if b]
        name = " ".join(bits) or f"USB {self.vid:04X}:{self.pid:04X}"
        return f"{name} ({self.vid:04X}:{self.pid:04X})"

    def interfaces_of_class(self, cls):
        return [i for i in self.interfaces if i.cls == cls]

    def __repr__(self):
        return f"<USB {self.vid:04X}:{self.pid:04X} {self.manufacturer}/{self.product}>"


# --------------------------------------------------------------- enumeration

def _read_string(getter):
    try:
        value = getter()
        return value if value else ""
    except Exception:
        return ""


def enumerate_devices() -> list:
    """Return every USB device currently attached to the phone."""
    manager = usb_manager()
    device_list = manager.getDeviceList()
    devices = []
    try:
        names = list(device_list.keySet().toArray())
    except Exception:
        names = []
    for name in names:
        jdev = device_list.get(name)
        if jdev is None:
            continue
        interfaces = []
        try:
            count = int(jdev.getInterfaceCount())
        except Exception:
            count = 0
        for idx in range(count):
            jintf = jdev.getInterface(idx)
            endpoints = []
            try:
                ep_count = int(jintf.getEndpointCount())
            except Exception:
                ep_count = 0
            for e in range(ep_count):
                jep = jintf.getEndpoint(e)
                endpoints.append(Endpoint(
                    address=int(jep.getAddress()) & 0xFF,
                    direction=int(jep.getDirection()),
                    type_=int(jep.getType()),
                    max_packet_size=int(jep.getMaxPacketSize()),
                    interval=int(jep.getInterval()),
                    number=int(jep.getEndpointNumber()),
                ))
            interfaces.append(Interface(
                index=idx,
                interface_id=int(jintf.getId()),
                cls=int(jintf.getInterfaceClass()) & 0xFF,
                subclass=int(jintf.getInterfaceSubclass()) & 0xFF,
                protocol=int(jintf.getInterfaceProtocol()) & 0xFF,
                endpoints=endpoints,
            ))
        devices.append(Device(
            jdevice=jdev,
            vid=int(jdev.getVendorId()) & 0xFFFF,
            pid=int(jdev.getProductId()) & 0xFFFF,
            manufacturer=_read_string(jdev.getManufacturerName),
            product=_read_string(jdev.getProductName),
            serial=_read_string(jdev.getSerialNumber),
            interfaces=interfaces,
        ))
    return devices


# --------------------------------------------------------------- permissions

def has_permission(device: Device) -> bool:
    try:
        return bool(usb_manager().hasPermission(device.jdevice))
    except Exception as e:
        logger.error("hasPermission failed: " + str(e))
        return False


def request_permission(device: Device, timeout: float = 25.0,
                       poll_interval: float = 0.25) -> bool:
    """Ask Android for access to `device` and wait for the user's answer.

    Must be called from a background thread (it blocks up to `timeout`
    seconds). Returns True when access was granted.

    Why this polls instead of listening for the broadcast
    ----------------------------------------------------
    The obvious implementation registers a BroadcastReceiver, which with
    pyjnius means subclassing PythonJavaClass - and that needs the Java class
    `org.jnius.NativeInvocationHandler` to be present in the APK.

    It is not, on current toolchains: p4a builds pyjnius as a
    PyProjectRecipe, and when a prebuilt Android wheel is available it takes
    the `install_prebuilt_wheel()` path and skips `build_arch()` entirely -
    so `postbuild_arch()`, the step that copies `jnius/src/org` into the
    project's Java sources, never runs. The symptom is exactly what showed up
    on device:

        java.lang.ClassNotFoundException: Didn't find class
        "org.jnius.NativeInvocationHandler"

    Polling `UsbManager.hasPermission()` needs no Python->Java interface at
    all, so it works regardless of whether those Java classes were shipped.
    The PendingIntent still has to exist because requestPermission() requires
    one; the broadcast it fires is simply ignored.
    """
    if has_permission(device):
        return True

    from jnius import autoclass

    act = activity()
    Intent = autoclass("android.content.Intent")
    PendingIntent = autoclass("android.app.PendingIntent")

    intent = Intent(ACTION_USB_PERMISSION)
    try:
        intent.setPackage(act.getPackageName())
    except Exception as e:
        logger.debug("setPackage failed: " + str(e))

    # FLAG_IMMUTABLE (1 << 26) is mandatory on Android 12+;
    # FLAG_UPDATE_CURRENT (1 << 27) reuses the PendingIntent on a retry.
    flags = (1 << 26) | (1 << 27)
    try:
        pi = PendingIntent.getBroadcast(act, 0, intent, flags)
    except Exception as e:
        raise UsbError(f"PendingIntent.getBroadcast failed: {e}")

    try:
        usb_manager().requestPermission(device.jdevice, pi)
    except Exception as e:
        raise UsbError(f"requestPermission failed: {e}")

    deadline = time.monotonic() + max(float(timeout), 1.0)
    while True:
        if has_permission(device):
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(poll_interval)


# ---------------------------------------------------------------- connection

class Connection:
    """A claimed USB interface, with blocking bulk IN/OUT transfers."""

    def __init__(self, device: Device, interface: Interface, force: bool = True):
        self.device = device
        self.interface = interface
        self._conn = None
        manager = usb_manager()
        self._conn = manager.openDevice(device.jdevice)
        if self._conn is None:
            raise UsbError(t("err_open_device"))
        self._jintf = device.jdevice.getInterface(interface.index)
        claimed = self._conn.claimInterface(self._jintf, force)
        if not claimed:
            try:
                self._conn.close()
            except Exception:
                pass
            raise UsbError(t("err_claim_failed"))
        self.ep_in = interface.ep_in
        self.ep_out = interface.ep_out
        if self.ep_out is None or self.ep_in is None:
            self.close()
            raise UsbError(t("err_no_endpoints"))

    # ------------------------------------------------------------ transfers

    def write(self, data, timeout: int = 3000) -> int:
        payload = bytes(data)
        n = self._conn.bulkTransfer(self._jep_out(), payload, len(payload), timeout)
        if n is None or n < 0:
            raise UsbError(f"bulk OUT failed (ret={n})")
        if n != len(payload):
            raise UsbError(f"short bulk OUT: {n}/{len(payload)} bytes")
        return n

    def read(self, length: int = None, timeout: int = 3000) -> bytes:
        size = int(length or self.ep_in.max_packet_size or 64)
        size = max(size, 64)
        buf = bytearray(size)
        n = self._conn.bulkTransfer(self._jep_in(), buf, size, timeout)
        if n is None or n < 0:
            raise UsbError(f"bulk IN failed (ret={n})")
        return bytes(buf[:n])

    def control_in(self, request_type: int, request: int, value: int, index: int,
                   length: int, timeout: int = 2000) -> bytes:
        buf = bytearray(length)
        n = self._conn.controlTransfer(request_type, request, value, index, buf, length, timeout)
        if n is None or n < 0:
            raise UsbError(f"control IN failed (ret={n})")
        return bytes(buf[:n])

    # ------------------------------------------------------------ internals

    def _jep_in(self):
        return self._jintf.getEndpoint(self._index_of_ep(self.ep_in))

    def _jep_out(self):
        return self._jintf.getEndpoint(self._index_of_ep(self.ep_out))

    def _index_of_ep(self, ep: Endpoint):
        for i, candidate in enumerate(self.interface.endpoints):
            if candidate.address == ep.address:
                return i
        raise UsbError("endpoint not found in interface")

    def close(self):
        if self._conn is not None:
            try:
                self._conn.releaseInterface(self._jintf)
            except Exception:
                pass
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
