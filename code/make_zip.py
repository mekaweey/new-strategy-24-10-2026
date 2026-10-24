# -*- coding: utf-8 -*-
"""Create the <1GB delivery zip from the package root.

Excludes caches and any existing zip. The resulting archive contains the
directory `strategy-audit/` at its root.
"""
from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT.parent / "strategy-audit.zip"
EXCLUDE_DIRS = {"__pycache__", ".git", ".venv", "venv"}
EXCLUDE_NAMES = {"strategy-audit.zip"}


def included(p: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in p.parts):
        return False
    if p.name in EXCLUDE_NAMES:
        return False
    if p.name.endswith(".pyc"):
        return False
    return p.is_file()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


files = sorted([p for p in ROOT.rglob("*") if included(p)],
               key=lambda p: p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED,
                     compresslevel=6, allowZip64=True) as z:
    for p in files:
        z.write(p, "strategy-audit/" + p.relative_to(ROOT).as_posix())

size = ZIP.stat().st_size
print(f"zip={ZIP}")
print(f"files={len(files)}")
print(f"size_bytes={size}")
print(f"size_mib={size/1024/1024:.1f}")
print(f"sha256={sha256(ZIP)}")
assert size < 1_000_000_000, f"zip too large: {size}"
