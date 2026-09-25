"""
CTAPHID (FIDO over USB HID) transport for the FIDO channel.

Android has no HIDAPI and no /dev/hidraw, so the 64-byte FIDO reports are sent
with bulk transfers on the HID interface's interrupt endpoints (that works with
the Android USB Host API as long as the kernel HID driver has been detached,
which usbhost.Connection does by claiming with force=True).

Supported here:
  * CTAPHID_INIT  (0x86) - allocate a channel, read device capabilities
  * CTAPHID_WINK  (0x88) - blink the LED, the fastest "is it alive?" test
  * CTAPHID_CBOR  (0x90) - raw CTAP2 request/response (used for getInfo)
"""

from __future__ import annotations

import os
import struct

from .cbor_mini import loads
from .pk.core.log import get_logger

logger = get_logger("ctap")

CTAPHID_PING = 0x81
CTAPHID_MSG = 0x83
CTAPHID_LOCK = 0x84
CTAPHID_INIT = 0x86
CTAPHID_WINK = 0x88
CTAPHID_CBOR = 0x90
CTAPHID_CANCEL = 0x91
CTAPHID_KEEPALIVE = 0xBB
CTAPHID_ERROR = 0xBF

BROADCAST_CID = 0xFFFFFFFF

CTAP2_GET_INFO = 0x04
CTAP2_RESET = 0x07

CAP_WINK = 0x01
CAP_CBOR = 0x04
CAP_NMSG = 0x08


class CTAPError(Exception):
    pass


class CTAPHIDTransport:
    def __init__(self, connection, packet_size: int = 64):
        self._conn = connection
        self.packet_size = packet_size
        self.cid = BROADCAST_CID
        self._init_response = None

    # ------------------------------------------------------------- framing

    def _write_frame(self, cid: int, cmd: int, data: bytes):
        """Send one CTAPHID message, splitting it into INIT + CONT packets."""
        payload = bytes(data)
        frame = bytearray(self.packet_size)
        frame[0:4] = struct.pack(">I", cid & 0xFFFFFFFF)
        frame[4] = (cmd | 0x80) & 0xFF
        frame[5] = (len(payload) >> 8) & 0xFF
        frame[6] = len(payload) & 0xFF
        head = payload[:self.packet_size - 7]
        frame[7:7 + len(head)] = head
        written = self._conn.write(bytes(frame), timeout=3000)
        if written != self.packet_size:
            raise CTAPError(f"short HID write: {written}/{self.packet_size}")

        rest = payload[self.packet_size - 7:]
        seq = 0
        while rest:
            cont = bytearray(self.packet_size)
            cont[0:4] = struct.pack(">I", cid & 0xFFFFFFFF)
            cont[4] = seq & 0x7F
            chunk = rest[:self.packet_size - 5]
            cont[5:5 + len(chunk)] = chunk
            written = self._conn.write(bytes(cont), timeout=3000)
            if written != self.packet_size:
                raise CTAPError(f"short HID continuation write: {written}")
            rest = rest[self.packet_size - 5:]
            seq += 1

    def _read_frame(self, timeout: int = 3000):
        """Read one CTAPHID response. Returns (cmd, payload).

        Per spec BCNTH/BCNTL counts the data only - the command byte lives at
        offset 4 of the INIT packet and is NOT part of the counted length.
        """
        first = self._conn.read(length=self.packet_size, timeout=timeout)
        if len(first) < 7:
            raise CTAPError("short HID report")
        resp_cmd = first[4]                        # 0x86 INIT, 0x90 CBOR, 0xBB KEEPALIVE
        bcnt = (first[5] << 8) | first[6]
        data = bytearray(first[7:])
        seq = 0
        while len(data) < bcnt:
            cont = self._conn.read(length=self.packet_size, timeout=timeout)
            if len(cont) < 5:
                raise CTAPError("short continuation report")
            if cont[4] != seq:
                raise CTAPError(f"continuation sequence mismatch (got {cont[4]}, want {seq})")
            data += cont[5:]
            seq = (seq + 1) & 0x7F
        return resp_cmd, bytes(data[:bcnt])

    def _exchange(self, cmd: int, payload: bytes = b"", timeout: int = 3000):
        self._write_frame(self.cid, cmd, payload)
        while True:
            resp_cmd, data = self._read_frame(timeout=timeout)
            if resp_cmd == CTAPHID_KEEPALIVE:
                continue                       # device still busy, keep waiting
            if resp_cmd != cmd:
                raise CTAPError(f"unexpected response command 0x{resp_cmd:02X}")
            return data

    # ------------------------------------------------------- public commands

    def init(self) -> dict:
        nonce = os.urandom(8)
        resp = self._exchange(CTAPHID_INIT, nonce)
        if len(resp) < 17:
            raise CTAPError("truncated CTAPHID_INIT response")
        self.cid = struct.unpack(">I", resp[8:12])[0]
        self._init_response = {
            "nonce_echo": resp[0:8],
            "cid": self.cid,
            "protocol_version": resp[12],
            "device_version": (resp[13], resp[14], resp[15]),
            "capabilities": resp[16],
        }
        return self._init_response

    @property
    def capabilities(self) -> dict:
        caps = (self._init_response or {}).get("capabilities", 0)
        return {"wink": bool(caps & CAP_WINK),
                "cbor": bool(caps & CAP_CBOR),
                "nmsg": bool(caps & CAP_NMSG)}

    def wink(self) -> bool:
        self._exchange(CTAPHID_WINK, b"", timeout=3000)
        return True

    def cbor(self, ctap_cmd: int, payload: bytes = b"", timeout: int = 5000):
        """Send a CTAP2 command; returns (status_byte, response_bytes)."""
        resp = self._exchange(CTAPHID_CBOR, bytes([ctap_cmd]) + payload, timeout=timeout)
        if not resp:
            raise CTAPError("empty CTAP2 response")
        return resp[0], resp[1:]

    def get_info(self) -> dict:
        status, data = self.cbor(CTAP2_GET_INFO)
        if status != 0x00:
            raise CTAPError(f"authenticatorGetInfo failed, status 0x{status:02X}")
        info = loads(data)
        if not isinstance(info, dict):
            raise CTAPError("authenticatorGetInfo did not return a CBOR map")
        return info

    def reset(self) -> bool:
        """Factory reset of the FIDO applet. Needs physical touch on the key."""
        status, _ = self.cbor(CTAP2_RESET, b"", timeout=30000)
        return status == 0x00

    # -------------------------------------------------------- lifecycle

    def reconnect(self):
        raise CTAPError("HID transport cannot be reopened; rescan the device")

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass


def describe(info: dict) -> dict:
    """Flatten the interesting parts of an authenticatorGetInfo response."""
    def s(v):
        return v.decode("utf-8", "replace") if isinstance(v, (bytes, bytearray)) else str(v)

    out = {}
    versions = info.get(1) or []
    out["versions"] = [s(v) for v in versions]
    if 2 in info:
        out["extensions"] = [s(v) for v in info[2]]
    aaguid = info.get(3)
    if isinstance(aaguid, (bytes, bytearray)):
        out["aaguid"] = aaguid.hex()
    opts = info.get(4) or {}
    out["options"] = {s(k): bool(v) for k, v in opts.items()} if isinstance(opts, dict) else {}
    if 5 in info:
        out["max_msg_size"] = info[5]
    pins = info.get(6) or []
    out["pin_uv_protocols"] = list(pins)
    if 7 in info:
        out["max_credential_count"] = info[7]
    if 8 in info:
        out["max_credential_id_length"] = info[8]
    if 9 in info:
        out["transports"] = [s(v) for v in info[9]]
    if 0x0A in info:
        out["algorithms"] = info[0x0A]
    return out
