#!/usr/bin/env python3
"""Create the distributable MatchIQ UCL dataset ZIP and checksum."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PACKAGE_ROOT.parent
ZIP_PATH = OUTPUT_DIR / "MatchIQ_UCL_Dataset_Ready.zip"
CHECKSUM_PATH = OUTPUT_DIR / "MatchIQ_UCL_Dataset_Ready.sha256.txt"
INVENTORY_PATH = PACKAGE_ROOT / "reports" / "package_inventory.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def distributable_files() -> list[Path]:
    files: list[Path] = []
    for path in sorted(PACKAGE_ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(PACKAGE_ROOT)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if path.name.endswith(".inspect.ndjson") or path.name.startswith("qa_"):
            continue
        files.append(path)
    return files


def main() -> None:
    files_before_inventory = [
        path for path in distributable_files() if path != INVENTORY_PATH
    ]
    inventory = {
        "package": PACKAGE_ROOT.name,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "excluded_support_artifacts": ["*.inspect.ndjson", "reports/qa_*.png"],
        "file_count_excluding_inventory": len(files_before_inventory),
        "files": [
            {
                "path": path.relative_to(PACKAGE_ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in files_before_inventory
        ],
    }
    INVENTORY_PATH.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    files = distributable_files()
    with ZipFile(ZIP_PATH, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(PACKAGE_ROOT)
            archive.write(path, Path(PACKAGE_ROOT.name) / relative)

    zip_digest = sha256(ZIP_PATH)
    CHECKSUM_PATH.write_text(
        f"{zip_digest}  {ZIP_PATH.name}\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "zip": str(ZIP_PATH),
                "bytes": ZIP_PATH.stat().st_size,
                "sha256": zip_digest,
                "files": len(files),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
