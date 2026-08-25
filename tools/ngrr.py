"""
ngrr.py - reader/writer for Native Instruments Guitar Rig preset files (.ngrr)

Container layout (little-endian), reverse-engineered from Guitar Rig 4/5/6 presets:

    magic   "-in-"                                   4 bytes
    version u32                                      (observed: 2)
    ident   "#NI#CS#Document##NI#SoundShell#Sound#"   37 bytes
    pad     0x00 * 11
    const   u32                                       (observed: 0x145 in every file)
    chunks  ...                                       until EOF

Each chunk:

    tag      "atad"        ("data" reversed)
    version  u32
    name     4 bytes       "dnss" / "ofni" / "tsrp" / "DNSS"  (reversed 4CCs)
    codec    "bilz"        ("zlib" reversed)
    comp_len u32           compressed byte count
    orig_len u32           uncompressed byte count
    payload  comp_len bytes of raw zlib stream

Chunk payloads:

    dnss / DNSS   16-byte sentinel markers that open and close the sound container
    ofni          plain UTF-8 XML  (<soundinfo>: preset name, bank, tags)
    tsrp          " LMX" ("XML " reversed) + u32 version + u32 xml_len + UTF-8 XML
                  (<gr-instrument-chunk>: the rack, components and parameters)
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass, field

MAGIC = b"-in-"
IDENT = b"#NI#CS#Document##NI#SoundShell#Sound#"
CHUNK_TAG = b"atad"
CODEC_TAG = b"bilz"
XML_TAG = b" LMX"
HEADER_LEN = 0x3C
CHUNK_HEADER_LEN = 24


class NgrrError(Exception):
    pass


@dataclass
class Chunk:
    version: int
    name: bytes
    data: bytes  # uncompressed payload
    raw: bytes | None = None  # original compressed bytes, reused when unmodified

    @property
    def label(self) -> str:
        return self.name.decode("latin-1")

    def serialize(self) -> bytes:
        comp = self.raw if self.raw is not None else zlib.compress(self.data, 9)
        return (
            CHUNK_TAG
            + struct.pack("<I", self.version)
            + self.name
            + CODEC_TAG
            + struct.pack("<II", len(comp), len(self.data))
            + comp
        )

    def replace(self, data: bytes) -> None:
        """Set new uncompressed payload; forces recompression on serialize."""
        self.data = data
        self.raw = None


@dataclass
class NgrrFile:
    header: bytes
    chunks: list[Chunk] = field(default_factory=list)

    # ---------- container ----------

    @classmethod
    def load(cls, path: str) -> "NgrrFile":
        with open(path, "rb") as fh:
            return cls.parse(fh.read())

    @classmethod
    def parse(cls, blob: bytes) -> "NgrrFile":
        if blob[:4] != MAGIC:
            raise NgrrError(f"bad magic {blob[:4]!r}, expected {MAGIC!r}")
        if blob[8 : 8 + len(IDENT)] != IDENT:
            raise NgrrError("missing NI SoundShell identifier")

        chunks: list[Chunk] = []
        off = HEADER_LEN
        while off < len(blob):
            if blob[off : off + 4] != CHUNK_TAG:
                raise NgrrError(f"expected chunk tag at 0x{off:x}, got {blob[off:off+4]!r}")
            version = struct.unpack_from("<I", blob, off + 4)[0]
            name = blob[off + 8 : off + 12]
            codec = blob[off + 12 : off + 16]
            if codec != CODEC_TAG:
                raise NgrrError(f"unsupported codec {codec!r} at 0x{off:x}")
            comp_len, orig_len = struct.unpack_from("<II", blob, off + 16)
            start = off + CHUNK_HEADER_LEN
            comp = blob[start : start + comp_len]
            if len(comp) != comp_len:
                raise NgrrError(f"truncated chunk {name!r} at 0x{off:x}")
            data = zlib.decompress(comp)
            if len(data) != orig_len:
                raise NgrrError(
                    f"chunk {name!r}: declared {orig_len} bytes, decompressed {len(data)}"
                )
            chunks.append(Chunk(version=version, name=name, data=data, raw=comp))
            off = start + comp_len

        return cls(header=blob[:HEADER_LEN], chunks=chunks)

    def serialize(self) -> bytes:
        return self.header + b"".join(c.serialize() for c in self.chunks)

    def save(self, path: str) -> None:
        with open(path, "wb") as fh:
            fh.write(self.serialize())

    def chunk(self, name: str) -> Chunk | None:
        want = name.encode("latin-1")
        for c in self.chunks:
            if c.name == want:
                return c
        return None

    # ---------- payloads ----------

    @property
    def soundinfo_xml(self) -> str | None:
        """The <soundinfo> metadata document (preset name, bank, tags)."""
        c = self.chunk("ofni")
        return None if c is None else c.data.decode("utf-8")

    @soundinfo_xml.setter
    def soundinfo_xml(self, xml: str) -> None:
        c = self.chunk("ofni")
        if c is None:
            raise NgrrError("no 'ofni' chunk in this file")
        c.replace(xml.encode("utf-8"))

    @property
    def rack_xml(self) -> str | None:
        """The <gr-instrument-chunk> document: rack, components, parameters."""
        c = self.chunk("tsrp")
        if c is None:
            return None
        payload = c.data
        if payload[:4] != XML_TAG:
            raise NgrrError(f"unexpected prst payload tag {payload[:4]!r}")
        _ver, xml_len = struct.unpack_from("<II", payload, 4)
        return payload[12 : 12 + xml_len].decode("utf-8")

    @rack_xml.setter
    def rack_xml(self, xml: str) -> None:
        c = self.chunk("tsrp")
        if c is None:
            raise NgrrError("no 'tsrp' chunk in this file")
        ver = struct.unpack_from("<I", c.data, 4)[0]
        body = xml.encode("utf-8")
        c.replace(XML_TAG + struct.pack("<II", ver, len(body)) + body)
