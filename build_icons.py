#!/usr/bin/env python3
"""
PandaPilot Build Script
=======================
Converts app/resources/icon.png into platform-native icon formats using Pillow.
Does NOT import PySide6 or Qt to remain safe in headless CI environments.

Usage:
    python build_icons.py
"""

import sys
import struct
import zlib
from pathlib import Path


def generate_ico(img_rgba: bytes, width: int, height: int, out_path: Path) -> None:
    """Write a minimal multi-resolution .ico file from a single RGBA PNG-encoded image."""
    try:
        from PIL import Image
        img = Image.open(out_path.parent.parent / "resources" / "icon.png").convert("RGBA")
        sizes = [256, 128, 64, 48, 32, 16]
        img.save(str(out_path), format="ICO", sizes=[(s, s) for s in sizes])
        print(f"  ✅ Generated {out_path.name} with sizes: {sizes}")
    except Exception as e:
        print(f"  ❌ Failed to generate ICO: {e}", file=sys.stderr)
        sys.exit(1)


def generate_icns(img_path: Path, out_path: Path) -> None:
    """Write a macOS .icns file from the source PNG using Pillow."""
    try:
        from PIL import Image

        # ICNS icon type map: (size, type_code)
        ICNS_ENTRIES = [
            (16,   b'icp4'),
            (32,   b'icp5'),
            (64,   b'icp6'),
            (128,  b'ic07'),
            (256,  b'ic08'),
            (512,  b'ic09'),
            (1024, b'ic10'),
            (32,   b'ic11'),  # Retina 16pt
            (64,   b'ic12'),  # Retina 32pt
            (256,  b'ic13'),  # Retina 128pt
            (512,  b'ic14'),  # Retina 256pt
        ]

        src = Image.open(img_path).convert("RGBA")

        import io
        data_chunks = []
        for size, type_code in ICNS_ENTRIES:
            resized = src.resize((size, size), Image.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            png_bytes = buf.getvalue()
            chunk_size = 8 + len(png_bytes)
            data_chunks.append(type_code + struct.pack(">I", chunk_size) + png_bytes)

        total_size = 8 + sum(len(c) for c in data_chunks)
        with open(out_path, "wb") as f:
            f.write(b'icns')
            f.write(struct.pack(">I", total_size))
            for chunk in data_chunks:
                f.write(chunk)

        print(f"  ✅ Generated {out_path.name} ({total_size / 1024:.1f} KB)")
    except Exception as e:
        print(f"  ❌ Failed to generate ICNS: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    resources_dir = Path(__file__).parent / "app" / "resources"
    icon_png = resources_dir / "icon.png"

    if not icon_png.exists():
        print(f"❌ Source icon not found: {icon_png}", file=sys.stderr)
        sys.exit(1)

    print(f"🎨 Generating native icons from: {icon_png}")

    # Windows .ico
    ico_out = resources_dir / "icon.ico"
    generate_ico(None, 256, 256, ico_out)

    # macOS .icns
    icns_out = resources_dir / "icon.icns"
    generate_icns(icon_png, icns_out)

    print("✅ All icons generated successfully.")


if __name__ == "__main__":
    main()
