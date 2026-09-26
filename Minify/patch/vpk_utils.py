import binascii
import hashlib
import os
import shutil
import struct
import threading
from concurrent.futures import ThreadPoolExecutor

import vpk
from core import base, config, constants, fs, log, output, utils

DEFAULT_VPK_CHUNK_SIZE = 100 * 1024 * 1024


def pack(source_dir, output_vpk_dir_path, chunk_size=DEFAULT_VPK_CHUNK_SIZE):
    """
    Packs source_dir into a multi-chunk VPK v2 archive (pak66_dir.vpk + pak66_000.vpk, ...).
    Each chunk file is capped at chunk_size bytes.
    """
    base_name = os.path.splitext(output_vpk_dir_path)[0]
    chunk_prefix = base_name[:-4] if base_name.endswith("_dir") else base_name
    output_dir = os.path.dirname(output_vpk_dir_path) or "."
    fs.create_dirs(output_dir)

    # Clean up any existing dir and chunk files for this prefix
    prefix_filename = os.path.basename(chunk_prefix)
    if os.path.isdir(output_dir):
        for item in os.listdir(output_dir):
            if item.startswith(f"{prefix_filename}_") and item.endswith(".vpk"):
                fs.remove_path(os.path.join(output_dir, item))

    # Collect files into extension -> relpath -> [(filename_no_ext, full_filename, abs_path)]
    tree = {}
    for root, _, filenames in os.walk(source_dir):
        rel = os.path.relpath(root, source_dir).replace("\\", "/")
        if rel == ".":
            rel = " "

        for filename in filenames:
            parts = filename.rsplit(".", 1)
            if len(parts) == 1:
                name, ext = parts[0], " "
            else:
                name, ext = parts[0], parts[1]

            tree.setdefault(ext, {}).setdefault(rel, []).append((name, filename, os.path.join(root, filename)))

    # Calculate tree length in bytes
    tree_length = 0
    for ext, relpaths in tree.items():
        tree_length += len(ext.encode("utf-8")) + 2
        for relpath, file_entries in relpaths.items():
            tree_length += len(relpath.encode("utf-8")) + 2
            for name, _, _ in file_entries:
                tree_length += len(name.encode("utf-8")) + 1 + 18
    tree_length += 1

    # Write chunk data files
    file_entries_meta = {}  # abs_path -> (crc, archive_idx, offset, length)
    current_chunk_idx = 0
    current_chunk_size = 0
    current_chunk_file = None

    def open_chunk_file(idx):
        return open(f"{chunk_prefix}_{idx:03d}.vpk", "wb")

    try:
        current_chunk_file = open_chunk_file(current_chunk_idx)
        for ext, relpaths in tree.items():
            for relpath, file_entries in relpaths.items():
                for name, full_name, src_path in file_entries:
                    file_size = os.path.getsize(src_path)
                    if current_chunk_size > 0 and (current_chunk_size + file_size > chunk_size):
                        current_chunk_file.close()
                        current_chunk_idx += 1
                        current_chunk_size = 0
                        current_chunk_file = open_chunk_file(current_chunk_idx)

                    crc = 0
                    file_offset = current_chunk_file.tell()
                    with open(src_path, "rb") as f:
                        while chunk := f.read(65536):
                            crc = binascii.crc32(chunk, crc)
                            current_chunk_file.write(chunk)

                    current_chunk_size += file_size
                    file_entries_meta[src_path] = (crc & 0xFFFFFFFF, current_chunk_idx, file_offset, file_size)
    finally:
        if current_chunk_file:
            current_chunk_file.close()

    # Write _dir.vpk directory file
    with open(output_vpk_dir_path, "w+b") as f:
        # VPK2 header: signature (0x55aa1234), version (2), tree_length,
        # embed_chunk_len (0), chunk_hashes_len (0), self_hashes_len (48), sig_len (0)
        f.write(struct.pack("3I4I", 0x55AA1234, 2, tree_length, 0, 0, 48, 0))
        header_len = f.tell()

        tree_bytes = bytearray()
        for ext, relpaths in tree.items():
            tree_bytes.extend(ext.encode("utf-8") + b"\x00")
            for relpath, file_entries in relpaths.items():
                tree_bytes.extend(relpath.encode("utf-8") + b"\x00")
                for name, full_name, src_path in file_entries:
                    tree_bytes.extend(name.encode("utf-8") + b"\x00")
                    crc, archive_idx, offset, length = file_entries_meta[src_path]
                    tree_bytes.extend(struct.pack("IHHIIH", crc, 0, archive_idx, offset, length, 0xFFFF))
                tree_bytes.extend(b"\x00")
            tree_bytes.extend(b"\x00")
        tree_bytes.extend(b"\x00")

        assert len(tree_bytes) == tree_length, f"Tree length mismatch: expected {tree_length}, got {len(tree_bytes)}"
        f.write(tree_bytes)

        # Hashes: tree_checksum, chunk_hashes_checksum, file_checksum
        tree_checksum = hashlib.md5(tree_bytes).digest()
        chunk_hashes_checksum = hashlib.md5(b"").digest()

        f.seek(0)
        file_checksum = hashlib.md5()
        file_checksum.update(f.read(header_len + tree_length))
        file_checksum.update(tree_checksum)
        file_checksum.update(chunk_hashes_checksum)

        f.seek(header_len + tree_length)
        f.write(tree_checksum)
        f.write(chunk_hashes_checksum)
        f.write(file_checksum.digest())


def extract(vpk_to_extract_from, paths, path_to_extract_to=base.build_dir):
    if isinstance(paths, str):
        paths = [paths]

    vpk_lock = threading.Lock()

    def extract_file(path):
        if not os.path.exists(full_path := os.path.join(path_to_extract_to, path)):  # extract files from VPK only once
            output.add_text("&extracting_terminal", path, indent=True)
            with vpk_lock:
                pakfile = vpk_to_extract_from.get_file(path)

            if pakfile:
                fs.create_dirs(os.path.dirname(full_path))
                pakfile.save(full_path)
            else:
                log.write_warning(f"File not found in VPK: {path}")

    with ThreadPoolExecutor() as executor:
        executor.map(extract_file, paths)


def dump(vpk_obj, output_dir, check_exists=True):
    for filepath in vpk_obj:
        # Sanitize filepath to prevent invalid characters or quotes
        clean_path = filepath.strip().strip('"').strip("'").replace("\\", "/").lstrip("/")
        if not clean_path:
            continue

        full_path = os.path.join(output_dir, clean_path)
        if check_exists and os.path.exists(full_path):
            continue

        fs.create_dirs(os.path.dirname(full_path))
        vpk_obj.get_file(filepath).save(full_path)


def is_minify_pak(vpk_path):
    """
    Determines whether a VPK file was generated by Minify by checking for the
    metadata marker files that dump_metadata() packs into created Paks.
    """
    marker_files = ["minify_mods.json", "minify_vpk_mods.txt", "minify_version.txt"]

    try:
        pak = vpk.open(vpk_path)
        pak_files = set(pak)
    except Exception:
        return False
    return not pak_files.isdisjoint(marker_files)


def dump_metadata(target_dir, mod_name=None, vpk_mods=None, extra_lists=None):
    """
    Standardizes metadata files for generated Paks.
    - target_dir: Where to dump.
    - mod_name: If provided, creates {mod_name}.txt (for single mod patches).
    - vpk_mods: List of VPK mod names for minify_vpk_mods.txt.
    - extra_lists: Dict of {filename: [lines]} for additional metadata files.
    """
    if config.get("opt_out_vpk_metadata"):
        return

    # 1. Base Info
    if mod_name is None:
        shutil.copy(base.mods_config_dir, os.path.join(target_dir, "minify_mods.json"))
    else:
        open(os.path.join(target_dir, f"{mod_name}.txt"), "w").close()

    # 2. Lists
    if vpk_mods:
        with utils.open_utf8(os.path.join(target_dir, "minify_vpk_mods.txt"), "w") as f:
            f.write("\n".join(vpk_mods))

    if extra_lists:
        for filename, lines in extra_lists.items():
            with utils.open_utf8(os.path.join(target_dir, filename), "w") as f:
                f.write("\n".join(lines))

    # 3. Minify Version
    with utils.open_utf8(os.path.join(target_dir, "minify_version.txt"), "w") as f:
        f.write(base.VERSION)

    # 4. Dota Version (steam.inf)
    if os.path.exists(constants.dota_steam_inf_path):
        shutil.copy(constants.dota_steam_inf_path, os.path.join(target_dir, "steam.inf"))
