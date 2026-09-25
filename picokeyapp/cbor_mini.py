"""
Tiny dependency-free CBOR decoder (and a small encoder).

The FIDO/CTAP2 channel answers with CBOR; pulling `cbor2` into an APK is
possible but one more recipe to break at build time, and we only need to read
`authenticatorGetInfo` responses. This implements RFC 7049 major types 0..5
and 7 (with 16/32/64-bit floats), which covers every CTAP2 response.
"""

from __future__ import annotations

import struct


class CBORError(ValueError):
    pass


class CBORDecoder:
    def __init__(self, data):
        self.data = bytes(data)
        self.pos = 0

    def _need(self, n):
        if self.pos + n > len(self.data):
            raise CBORError("truncated CBOR input")

    def _read(self, n):
        self._need(n)
        chunk = self.data[self.pos:self.pos + n]
        self.pos += n
        return chunk

    def _head(self):
        self._need(1)
        ib = self.data[self.pos]
        self.pos += 1
        major = ib >> 5
        ai = ib & 0x1F
        if ai < 24:
            return major, ai
        if ai == 24:
            return major, self._read(1)[0]
        if ai == 25:
            return major, struct.unpack(">H", self._read(2))[0]
        if ai == 26:
            return major, struct.unpack(">I", self._read(4))[0]
        if ai == 27:
            return major, struct.unpack(">Q", self._read(8))[0]
        if ai == 31:
            return major, None            # indefinite length / break
        raise CBORError(f"unsupported additional info {ai}")

    def decode(self):
        major, val = self._head()
        if major == 0:
            return val
        if major == 1:
            return -1 - val
        if major == 2:
            if val is None:               # indefinite length byte string
                out = b""
                while self.data[self.pos] != 0xFF:
                    out += self.decode()
                self.pos += 1
                return out
            return self._read(val)
        if major == 3:
            if val is None:
                out = ""
                while self.data[self.pos] != 0xFF:
                    out += self.decode()
                self.pos += 1
                return out
            return self._read(val).decode("utf-8", "replace")
        if major == 4:
            out = []
            if val is None:
                while self.data[self.pos] != 0xFF:
                    out.append(self.decode())
                self.pos += 1
            else:
                for _ in range(val):
                    out.append(self.decode())
            return out
        if major == 5:
            out = {}
            if val is None:
                while self.data[self.pos] != 0xFF:
                    k = self.decode()
                    out[k] = self.decode()
                self.pos += 1
            else:
                for _ in range(val):
                    k = self.decode()
                    out[k] = self.decode()
            return out
        if major == 6:
            return ("tag", val, self.decode())
        if major == 7:
            if val is None:
                return None
            if val == 20:
                return False
            if val == 21:
                return True
            if val == 22:
                return None
            if val == 23:                 # undefined
                return None
            if val == 25:
                return struct.unpack(">e", self._read(2))[0]
            if val == 26:
                return struct.unpack(">f", self._read(4))[0]
            if val == 27:
                return struct.unpack(">d", self._read(8))[0]
            return ("simple", val)
        raise CBORError(f"unsupported major type {major}")


def loads(data):
    """Decode one CBOR item. Extra trailing bytes are ignored on purpose."""
    return CBORDecoder(data).decode()


def dumps(obj) -> bytes:
    """Encode the subset needed to *send* CTAP2 commands (int/bytes/str/...)."""
    def head(major, val):
        if val < 24:
            return bytes([(major << 5) | val])
        if val < 256:
            return bytes([(major << 5) | 24, val])
        if val < 65536:
            return bytes([(major << 5) | 25]) + struct.pack(">H", val)
        if val < 2 ** 32:
            return bytes([(major << 5) | 26]) + struct.pack(">I", val)
        return bytes([(major << 5) | 27]) + struct.pack(">Q", val)

    if obj is None:
        return b"\xf6"
    if obj is True:
        return b"\xf5"
    if obj is False:
        return b"\xf4"
    if isinstance(obj, int):
        return head(0, obj) if obj >= 0 else head(1, -1 - obj)
    if isinstance(obj, bytes):
        return head(2, len(obj)) + obj
    if isinstance(obj, str):
        raw = obj.encode("utf-8")
        return head(3, len(raw)) + raw
    if isinstance(obj, (list, tuple)):
        return head(4, len(obj)) + b"".join(dumps(x) for x in obj)
    if isinstance(obj, dict):
        out = head(5, len(obj))
        for k, v in obj.items():
            out += dumps(k) + dumps(v)
        return out
    raise CBORError(f"cannot encode {type(obj)!r}")
