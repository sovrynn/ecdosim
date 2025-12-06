#!/usr/bin/env python3
"""
Batch text overlay for PNGs in a relative folder.

Usage:
  python add_overlay.py path/to/relative/folder

Writes processed images to "<folder>-overlay" next to the input folder.
"""

from pathlib import Path
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont

# =========================
# Config — edit these
# =========================
TEXT_LABEL = "ECDOsim v10 (by Junho): S1 -> S2 Strong (Frame `/160)"      # Use ` in string to insert frame number (e.g. "Frame `")
OFFSET_X = 15               # pixels from top-left corner (x)
OFFSET_Y = 10              # pixels from top-left corner (y)
FONT_PATH = "RobotoCondensed.ttf"     # path to .ttf font
FONT_SIZE = 32
FONT_COLOR = (255, 255, 255, 255)  # RGBA tuple (white)
# =========================


def load_font(font_path: str, size: int):
    """Try loading the specified font, fallback to default if unavailable."""
    try:
        return ImageFont.truetype(font_path, size=size)
    except Exception:
        print("[warn] Could not load font; falling back to default.")
        return ImageFont.load_default()


def add_text_overlay(img: Image.Image, text: str, x: int, y: int, font, color):
    """Return image with a text overlay at (x, y)."""
    if img.mode != "RGBA":
        base = img.convert("RGBA")
    else:
        base = img.copy()

    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.text((x, y), text, font=font, fill=color)

    return Image.alpha_composite(base, overlay)


def main():
    parser = argparse.ArgumentParser(description="Add a text overlay to all PNGs in a folder.")
    parser.add_argument("folder", help="Relative path to the input folder containing PNG files.")
    args = parser.parse_args()

    in_dir = Path(args.folder)
    if not in_dir.exists() or not in_dir.is_dir():
        print(f'[error] "{in_dir}" is not a directory.')
        sys.exit(1)

    out_dir = in_dir.parent / f"{in_dir.name}-overlay"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Sort filenames alphabetically to determine consistent frame order
    pngs = sorted([p for p in in_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"])
    total = len(pngs)
    if total == 0:
        print(f"[info] No PNG files found in {in_dir}")
        sys.exit(0)

    # Determine zero-padding width
    pad_width = len(str(total))
    font = load_font(FONT_PATH, FONT_SIZE)

    for idx, src in enumerate(pngs, start=1):
        try:
            with Image.open(src) as im:
                # Replace backtick with zero-padded frame number
                frame_str = str(idx).zfill(pad_width)
                overlay_text = TEXT_LABEL.replace("`", frame_str)

                result = add_text_overlay(im, overlay_text, OFFSET_X, OFFSET_Y, font, FONT_COLOR)

                # Preserve DPI metadata if possible
                save_kwargs = {}
                if "dpi" in im.info:
                    save_kwargs["dpi"] = im.info["dpi"]

                dst = out_dir / src.name
                result.save(dst, format="PNG", **save_kwargs)

            print(f"[{idx}/{total}] {src.name} -> {dst.relative_to(Path.cwd()) if dst.is_absolute() else dst}")
        except Exception as e:
            print(f"[error] Failed on {src.name}: {e}")

    print(f"[done] Wrote {total} file(s) to {out_dir}")


if __name__ == "__main__":
    main()
