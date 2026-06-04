#!/usr/bin/env python3
"""Extract Noto Sans CJK TC Regular/Bold OTF from system .ttc (no network)."""
from pathlib import Path

from fontTools.ttLib import TTCollection

TTC_REG = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
TTC_BOLD = Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
OUT = Path.home() / ".local/share/fonts/noto-sans-cjk-tc"
OUT.mkdir(parents=True, exist_ok=True)

TARGET = "Noto Sans CJK TC"


def extract(ttc_path: Path, out_name: str) -> None:
    col = TTCollection(str(ttc_path))
    for i, font in enumerate(col):
        name = font["name"].getDebugName(4) or ""
        if TARGET in name:
            dest = OUT / out_name
            font.save(str(dest))
            print(f"Wrote {dest} ({dest.stat().st_size} bytes) from {ttc_path}[{i}] ({name})")
            return
    names = [f["name"].getDebugName(4) for f in col]
    raise SystemExit(f"{TARGET!r} not in {ttc_path}: {names}")


extract(TTC_REG, "NotoSansCJKtc-Regular.otf")
extract(TTC_BOLD, "NotoSansCJKtc-Bold.otf")
print(f"Done -> {OUT}")
