"""
Simple .mo file compiler for gettext .po files.

This is a basic implementation that doesn't require external tools.
It reads .po files and creates .mo files that gettext can use.
"""

import struct
import array
from pathlib import Path


def parse_po_file(po_file: Path) -> dict[str, str]:
    """
    Parse a .po file and extract msgid/msgstr pairs.

    Args:
        po_file: Path to .po file

    Returns:
        Dictionary mapping msgid to msgstr
    """
    translations = {}
    current_msgid = None
    current_msgstr = None
    in_msgid = False
    in_msgstr = False

    with open(po_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Start of msgid
            if line.startswith('msgid '):
                if current_msgid and current_msgstr is not None:
                    translations[current_msgid] = current_msgstr
                current_msgid = line[6:].strip('"')
                in_msgid = True
                in_msgstr = False
                current_msgstr = None
                continue

            # Start of msgstr
            if line.startswith('msgstr '):
                current_msgstr = line[7:].strip('"')
                in_msgid = False
                in_msgstr = True
                continue

            # Continuation line
            if line.startswith('"') and line.endswith('"'):
                text = line[1:-1]
                if in_msgid and current_msgid is not None:
                    current_msgid += text
                elif in_msgstr and current_msgstr is not None:
                    current_msgstr += text

        # Don't forget the last entry
        if current_msgid and current_msgstr is not None:
            translations[current_msgid] = current_msgstr

    # Remove the header entry (empty msgid)
    translations.pop('', None)

    return translations


def generate_mo_file(translations: dict[str, str], mo_file: Path) -> None:
    """
    Generate a .mo file from translations dictionary.

    Args:
        translations: Dictionary mapping msgid to msgstr
        mo_file: Path where .mo file should be written
    """
    # Prepare strings as bytes
    keys = sorted(translations.keys())
    ids = [key.encode('utf-8') for key in keys]
    strs = [translations[key].encode('utf-8') for key in keys]

    # The .mo file format is documented in the gettext manual
    # It uses a binary format with a header and two string tables

    keystart = 7 * 4 + 16 * len(keys)
    valuestart = keystart + sum(len(id) + 1 for id in ids)

    # Build the key and value tables
    koffsets = []
    voffsets = []

    # Key table
    offset = 0
    for id in ids:
        koffsets.append((len(id), keystart + offset))
        offset += len(id) + 1

    # Value table
    offset = 0
    for str in strs:
        voffsets.append((len(str), valuestart + offset))
        offset += len(str) + 1

    # Generate the .mo file
    with open(mo_file, 'wb') as f:
        # Magic number
        f.write(struct.pack('I', 0x950412de))
        # Version
        f.write(struct.pack('I', 0))
        # Number of entries
        f.write(struct.pack('I', len(keys)))
        # Offset to key table
        f.write(struct.pack('I', 7 * 4))
        # Offset to value table
        f.write(struct.pack('I', 7 * 4 + len(keys) * 8))
        # Hash table size (not used)
        f.write(struct.pack('I', 0))
        # Hash table offset (not used)
        f.write(struct.pack('I', 0))

        # Write key table
        for length, offset in koffsets:
            f.write(struct.pack('I', length))
            f.write(struct.pack('I', offset))

        # Write value table
        for length, offset in voffsets:
            f.write(struct.pack('I', length))
            f.write(struct.pack('I', offset))

        # Write keys
        for id in ids:
            f.write(id)
            f.write(b'\x00')

        # Write values
        for str in strs:
            f.write(str)
            f.write(b'\x00')


def compile_po_to_mo(po_file: Path) -> Path:
    """
    Compile a .po file to .mo format.

    Args:
        po_file: Path to .po file

    Returns:
        Path to generated .mo file
    """
    translations = parse_po_file(po_file)
    mo_file = po_file.with_suffix('.mo')
    generate_mo_file(translations, mo_file)
    return mo_file


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python mo_compiler.py <file.po>")
        sys.exit(1)

    po_file = Path(sys.argv[1])
    if not po_file.exists():
        print(f"Error: {po_file} not found")
        sys.exit(1)

    mo_file = compile_po_to_mo(po_file)
    print(f"Compiled: {po_file} -> {mo_file}")
