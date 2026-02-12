import os
import struct


def rva_to_file_offset(f, rva, e_lfanew, num_sections, section_table_offset):
    """Convert an RVA to a file offset using the section table."""
    f.seek(section_table_offset)
    for _ in range(num_sections):
        sec = f.read(40)
        if len(sec) < 40:
            return 0
        vsize = struct.unpack_from('<I', sec, 8)[0]
        vaddr = struct.unpack_from('<I', sec, 12)[0]
        raw_size = struct.unpack_from('<I', sec, 16)[0]
        raw_ptr = struct.unpack_from('<I', sec, 20)[0]
        size = vsize if vsize else raw_size
        if vaddr <= rva < vaddr + size:
            delta = rva - vaddr
            if delta < raw_size:
                return raw_ptr + delta
    return 0


def is_arm64x(f, e_lfanew):
    """Check if an ARM64 PE is actually ARM64X by inspecting Load Config."""
    # COFF File Header: starts right after PE signature (4 bytes)
    file_hdr_off = e_lfanew + 4

    f.seek(file_hdr_off + 2)
    num_sections = struct.unpack('<H', f.read(2))[0]

    f.seek(file_hdr_off + 16)
    size_opt_hdr = struct.unpack('<H', f.read(2))[0]

    opt_hdr_off = file_hdr_off + 20  # Optional Header starts after 20-byte File Header

    # Verify PE32+ (Magic == 0x20b)
    f.seek(opt_hdr_off)
    magic = struct.unpack('<H', f.read(2))[0]
    if magic != 0x20B:
        return False

    # NumberOfRvaAndSizes at Optional Header + 108
    f.seek(opt_hdr_off + 108)
    num_dd = struct.unpack('<I', f.read(4))[0]
    if num_dd <= 10:
        return False

    # Load Config Directory entry (index 10) in Data Directory
    # Data Directory starts at Optional Header + 112
    f.seek(opt_hdr_off + 112 + 10 * 8)
    lc_rva, lc_size = struct.unpack('<II', f.read(8))
    if lc_rva == 0 or lc_size == 0:
        return False

    section_table_off = opt_hdr_off + size_opt_hdr
    lc_file_off = rva_to_file_offset(f, lc_rva, e_lfanew, num_sections, section_table_off)
    if lc_file_off == 0:
        return False

    # First DWORD of IMAGE_LOAD_CONFIG_DIRECTORY64 is Size
    f.seek(lc_file_off)
    lc_struct_size = struct.unpack('<I', f.read(4))[0]

    # CHPEMetadataPointer is at offset 0xC8 in IMAGE_LOAD_CONFIG_DIRECTORY64
    # Need struct size >= 0xD0 (0xC8 + 8) to contain this field
    if lc_struct_size < 0xD0:
        return False

    f.seek(lc_file_off + 0xC8)
    chpe_metadata_ptr = struct.unpack('<Q', f.read(8))[0]
    return chpe_metadata_ptr != 0


def get_pe_arch(filepath):
    """Detect the architecture of a PE file (DLL/EXE)."""
    try:
        with open(filepath, 'rb') as f:
            # DOS Header: e_lfanew at offset 0x3C
            f.seek(0x3C)
            data = f.read(4)
            if len(data) < 4:
                return "Error: File too small"
            e_lfanew = struct.unpack('<I', data)[0]

            # PE Signature
            f.seek(e_lfanew)
            if f.read(4) != b'PE\x00\x00':
                return "Error: Not a PE file"

            # Machine type (first 2 bytes of COFF File Header)
            machine = struct.unpack('<H', f.read(2))[0]

            MACHINE_MAP = {
                0x014C: "x86",
                0x8664: "x64",
                0x01C0: "ARM",
                0xAA64: "ARM64",
                0xA641: "ARM64EC",
            }
            arch = MACHINE_MAP.get(machine, f"Unknown (0x{machine:04x})")

            # For ARM64 binaries, check if it's actually ARM64X
            if machine == 0xAA64:
                try:
                    if is_arm64x(f, e_lfanew):
                        arch = "ARM64X"
                except Exception:
                    pass

            return arch
    except Exception as e:
        return f"Error: {e}"


def main():
    folder_path = '.'
    print(f"{'File Path':<60} {'Architecture'}")
    print("-" * 80)

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(('.dll', '.exe')):
                filepath = os.path.join(root, file)
                arch = get_pe_arch(filepath)
                rel_path = os.path.relpath(filepath, folder_path)
                print(f"{rel_path:<60} {arch}")


if __name__ == "__main__":
    main()
