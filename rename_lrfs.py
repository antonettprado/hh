#!/usr/bin/env python3
import re
from pathlib import Path
import sys

# Match "name": "SL_4j_resolved__..." but not already "SL_4j_resolved___..."
pattern = re.compile(r'("name"\s*:\s*")SL_4j_resolved__(?!_)')

def rename_in_place(path: Path):
    text = path.read_text()
    new_text, count = pattern.subn(r'\1SL_4j_resolved___', text)
    if count == 0:
        print(f"No changes made to {path}")
    else:
        path.write_text(new_text)
        print(f"Updated {count} name(s) in {path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <json_file>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    rename_in_place(file_path)