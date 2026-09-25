"""
Device / channel discovery.

A PicoKey exposes up to three usable USB interfaces and this module turns
whatever is present into a "channel" the UI can list and connect to:

    ccid    bInterfaceClass 0x0B   CCID/smartcard  -> APDU over CCID frames
    rescue  bInterfaceClass 0xFF   vendor specific -> APDU over CCID frames
    fido    bInterfaceClass 0x03   HID, usage page 0xF1D0 -> CTAPHID
"""

from __future__ import annotations

from . import usbhost
from .pk.core.log import get_logger

logger = get_logger("detect")

FIDO_USAGE_PAGE = bytes([0x06, 0xD0, 0xF1])     # Usage Page (FIDO Alliance)
KNOWN_VID_PIDS = {(0xFEFF, 0xFCFD)}             # upstream default
NAME_HINTS = ("picokey", "pico key", "pol henarejos", "pico keys", "picokeys")

KIND_INFO = {
    "ccid": ("CCID 智能卡通道", "走 CCID 帧的 APDU，功能最全（设备信息/PHY/安全启动/重启）"),
    "rescue": ("救援通道 (vendor 0xFF)", "固件没起来或 PC/SC 不可用时的备用通道，同样是 CCID 帧"),
    "fido": ("FIDO HID 通道", "CTAPHID：WINK 闪灯、authenticatorGetInfo、CTAP2 reset"),
}


class Channel:
    def __init__(self, kind: str, device, interface):
        self.kind = kind
        self.device = device
        self.interface = interface

    @property
    def title(self) -> str:
        name, _ = KIND_INFO.get(self.kind, (self.kind, ""))
        return name

    @property
    def detail(self) -> str:
        _, desc = KIND_INFO.get(self.kind, (self.kind, ""))
        return desc

    @property
    def label(self) -> str:
        return f"{self.device.label} · {self.title}"

    def __repr__(self):
        return f"<Channel {self.kind} {self.device.label}>"


def _looks_like_picokey(device) -> bool:
    blob = " ".join([device.manufacturer, device.product]).lower()
    if any(h in blob for h in NAME_HINTS):
        return True
    return (device.vid, device.pid) in KNOWN_VID_PIDS


def scan() -> list:
    """Return every plausible channel on every attached USB device."""
    try:
        devices = usbhost.enumerate_devices()
    except usbhost.UsbError as e:
        logger.error("enumeration failed: " + str(e))
        raise

    channels = []
    for dev in devices:
        intfs = dev.interfaces
        classes = {i.cls for i in intfs}

        for intf in intfs:
            if intf.cls == usbhost.USB_CLASS_SMARTCARD:
                channels.append(Channel("ccid", dev, intf))
            elif intf.cls == usbhost.USB_CLASS_VENDOR:
                # Upstream's rescue interface lives on a device that also
                # advertises the smartcard class, but the vendor interface is
                # usable on its own too - list it either way.
                channels.append(Channel("rescue", dev, intf))
            elif intf.cls == usbhost.USB_CLASS_HID and intf.subclass == 0 \
                    and intf.protocol == 0 and intf.ep_in and intf.ep_out:
                channels.append(Channel("fido", dev, intf))

        # nothing obvious? keep the device visible so the user can still try
        if not any(c.device is dev for c in channels):
            logger.debug(f"no known interface on {dev!r}")
    # PicoKeys first, then everything else
    channels.sort(key=lambda c: (not _looks_like_picokey(c.device), c.kind != "ccid"))
    return channels


def _check_fido(conn, interface) -> bool:
    try:
        desc = conn.control_in(0x81, usbhost.USB_REQ_GET_DESCRIPTOR,
                               (usbhost.HID_REPORT_DESCRIPTOR_TYPE << 8),
                               interface.id, 512)
    except Exception as e:
        logger.debug("HID report descriptor unavailable: " + str(e))
        return True                    # cannot verify -> let the user try anyway
    return FIDO_USAGE_PAGE in desc


def connect(channel: Channel, timeout: float = 15.0):
    """Open `channel`: request USB permission, claim the interface, build transport.

    Blocking: run it in a worker thread. Returns
      ("apdu", CCIDTransport)   for ccid / rescue
      ("ctap", CTAPHIDTransport) for fido
    """
    from . import ccid, ctap

    dev = channel.device
    if not usbhost.request_permission(dev, timeout=timeout):
        raise usbhost.UsbError("USB 权限被拒绝（弹窗里要点“允许”，并且只能点一次）")

    def _reopener():
        return usbhost.Connection(dev, channel.interface)

    if not usbhost.has_permission(dev):
        raise usbhost.UsbError("UsbManager 仍然没有权限")

    conn = usbhost.Connection(dev, channel.interface)

    if channel.kind == "fido":
        if not _check_fido(conn, channel.interface):
            conn.close()
            raise usbhost.UsbError("这个 HID 接口不像 FIDO 设备（报告描述符里没有 usage page 0xF1D0）")
        transport = ctap.CTAPHIDTransport(conn)
        return "ctap", transport

    from .pk import ConnectionType
    ctype = ConnectionType.SMARTCARD if channel.kind == "ccid" else ConnectionType.RESCUE
    transport = ccid.CCIDTransport(conn, label=channel.title, reopener=_reopener,
                                   connection_type=ctype)
    return "apdu", transport
