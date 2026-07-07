from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ERD_ROOT = Path(__file__).resolve().parents[1]
DFD_SOURCE = ERD_ROOT.parents[0] / "dfd" / "source"
sys.path.insert(0, str(DFD_SOURCE))

from render_mermaid_diagrams import EDGE_EXE, download_mermaid_js, render_svg_and_png


def main() -> None:
    if not EDGE_EXE.exists():
        raise SystemExit(f"Microsoft Edge not found at {EDGE_EXE}")

    cache_dir = Path(os.environ.get("TEMP", tempfile.gettempdir())) / "attendance_mermaid_cache"
    cache_dir.mkdir(exist_ok=True)
    mermaid_js_path = download_mermaid_js(cache_dir)

    source_path = ERD_ROOT / "source" / "attendance-system-erd.mmd"
    svg_path = ERD_ROOT / "attendance-system-erd.svg"
    png_path = ERD_ROOT / "attendance-system-erd.png"

    render_svg_and_png(
        source_path,
        "Normalized MySQL ERD - Attendance System",
        mermaid_js_path,
        svg_path,
        png_path,
    )

    print(f"Wrote {svg_path}")
    print(f"Wrote {png_path}")


if __name__ == "__main__":
    main()
