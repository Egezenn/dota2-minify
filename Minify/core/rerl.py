import os
import struct
from dataclasses import dataclass
from typing import Optional

from core import fs


@dataclass
class RERLEntry:
    id: int
    name: str


@dataclass
class ResourceBlock:
    entry_pos: int
    block_type: bytes
    type_name: str
    rel_offset: int
    abs_offset: int
    size: int


@dataclass
class CompiledResource:
    file_size: int
    header_version: int
    version: int
    block_offset: int
    block_count: int
    blocks: list[ResourceBlock]
    data: bytearray


def parse_resource(data: bytes | bytearray) -> CompiledResource:
    """Parses a Source 2 compiled resource header and block table."""
    buf = bytearray(data)
    file_size, header_version, version = struct.unpack_from("<IHH", buf, 0)
    block_offset, block_count = struct.unpack_from("<II", buf, 8)

    blocks: list[ResourceBlock] = []
    for i in range(block_count):
        entry_pos = 16 + i * 12
        b_type, b_offset, b_size = struct.unpack_from("<4sII", buf, entry_pos)
        type_name = b_type.decode("ascii", errors="ignore")
        abs_offset = entry_pos + 4 + b_offset
        blocks.append(
            ResourceBlock(
                entry_pos=entry_pos,
                block_type=b_type,
                type_name=type_name,
                rel_offset=b_offset,
                abs_offset=abs_offset,
                size=b_size,
            )
        )

    return CompiledResource(
        file_size=file_size,
        header_version=header_version,
        version=version,
        block_offset=block_offset,
        block_count=block_count,
        blocks=blocks,
        data=buf,
    )


def read_rerl(data: bytes | bytearray) -> list[RERLEntry]:
    """Extracts external references from a compiled resource's RERL block."""
    res = parse_resource(data)
    rerl_block = next((b for b in res.blocks if b.type_name == "RERL"), None)
    if not rerl_block or rerl_block.size == 0:
        return []

    abs_off = rerl_block.abs_offset
    offset_to_entries, count = struct.unpack_from("<II", res.data, abs_off)
    if count == 0:
        return []

    entries: list[RERLEntry] = []
    pos = abs_off + offset_to_entries
    for _ in range(count):
        m_id, str_rel_off, _pad = struct.unpack_from("<Qii", res.data, pos)
        str_abs_pos = pos + 8 + str_rel_off
        null_byte = res.data.find(b"\x00", str_abs_pos)
        if null_byte == -1:
            name = res.data[str_abs_pos:].decode("utf-8", errors="ignore")
        else:
            name = res.data[str_abs_pos:null_byte].decode("utf-8", errors="ignore")
        entries.append(RERLEntry(id=m_id, name=name))
        pos += 16

    return entries


def serialize_rerl(entries: list[RERLEntry]) -> bytes:
    """Serializes a list of RERLEntry items into a Source 2 RERL block payload."""
    if not entries:
        return struct.pack("<II", 0, 0)

    entry_size = 16
    current_string_offset = 0

    entries_buf = bytearray()
    strings_buf = bytearray()

    for i, entry in enumerate(entries):
        name_bytes = entry.name.encode("utf-8") + b"\x00"
        rel_offset = (len(entries) * entry_size + current_string_offset) - (8 + i * entry_size)
        entries_buf += struct.pack("<Qii", entry.id, rel_offset, 0)
        strings_buf += name_bytes
        current_string_offset += len(name_bytes)

    return struct.pack("<II", 8, len(entries)) + entries_buf + strings_buf


def patch_resource_rerl(data: bytes | bytearray, redirect_map: dict[str, str]) -> tuple[bytearray, int]:
    """
    Replaces external reference strings in the RERL block according to redirect_map.
    Returns (patched_data, replacement_count).
    """
    res = parse_resource(data)
    rerl_idx = next((i for i, b in enumerate(res.blocks) if b.type_name == "RERL"), None)
    if rerl_idx is None:
        return bytearray(data), 0

    rerl_block = res.blocks[rerl_idx]
    entries = read_rerl(res.data)
    if not entries:
        return bytearray(data), 0

    replacements_made = 0
    for entry in entries:
        if entry.name in redirect_map:
            entry.name = redirect_map[entry.name]
            replacements_made += 1

    if replacements_made == 0:
        return bytearray(data), 0

    new_rerl_bytes = serialize_rerl(entries)
    delta_size = len(new_rerl_bytes) - rerl_block.size

    # Update file size in header
    struct.pack_into("<I", res.data, 0, res.file_size + delta_size)

    # Update RERL block size in block table
    struct.pack_into("<I", res.data, rerl_block.entry_pos + 8, len(new_rerl_bytes))

    # Shift subsequent blocks in block table
    for block in res.blocks:
        if block.abs_offset > rerl_block.abs_offset:
            struct.pack_into("<I", res.data, block.entry_pos + 4, block.rel_offset + delta_size)

    # Splice new RERL payload
    part1 = res.data[: rerl_block.abs_offset]
    part2 = res.data[rerl_block.abs_offset + rerl_block.size :]
    patched_data = part1 + new_rerl_bytes + part2

    return patched_data, replacements_made


def patch_file(src_path: str, redirect_map: dict[str, str], dest_path: Optional[str] = None) -> bool:
    """
    Reads a compiled resource from src_path, applies RERL redirects, and writes to dest_path.
    If dest_path is None, overwrites src_path.
    Returns True if modifications were made.
    """
    if not os.path.exists(src_path):
        return False

    with open(src_path, "rb") as f:
        data = f.read()

    patched_data, count = patch_resource_rerl(data, redirect_map)
    if count == 0:
        return False

    out_path = dest_path or src_path
    fs.create_dirs(os.path.dirname(out_path))
    with open(out_path, "wb") as f:
        f.write(patched_data)

    return True
