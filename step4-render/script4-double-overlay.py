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
# --- First (top-left) overlay ---
TEXT_LABEL_TL = "ECDOsim v10 (Scenario: S1 -> S2 @2x Strength)"
OFFSET_X_TL = 15          # distance from left
OFFSET_Y_TL = 10          # distance from top
FONT_PATH_TL = "RobotoCondensed.ttf"
FONT_SIZE_TL = 32
FONT_COLOR_TL = (0, 0, 0, 255)

# --- Bottom-left overlay ---
TEXT_LABEL_BL = "~20 mm particles (~64 km³), Pivots: (-20 S,130 E), (20 N,-50 W)"
OFFSET_X_BL = 15          # distance from left
OFFSET_Y_BL = 10          # distance from bottom
FONT_PATH_BL = "RobotoCondensed.ttf"
FONT_SIZE_BL = 26
FONT_COLOR_BL = (0, 0, 0, 255)

# =========================


def load_font(font_path: str, size: int):
    """Try loading the specified font, fallback to default if unavailable."""
    try:
        return ImageFont.truetype(font_path, size=size)
    except Exception:
        print(f"[warn] Could not load font '{font_path}'; using default font.")
        return ImageFont.load_default()


def add_text_overlays(
    img, 
    text_top, xy_top, font_top, color_top,
    text_bottom, xy_bottom_from_bottom, font_bottom, color_bottom
):
    """Return image with two text overlays: top-left and bottom-left."""
    if img.mode != "RGBA":
        base = img.convert("RGBA")
    else:
        base = img.copy()

    W, H = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # --- Top-left text ---
    if text_top:
        draw.text(xy_top, text_top, font=font_top, fill=color_top)

    # --- Bottom-left text ---
    if text_bottom:
        x_bottom, y_offset_bottom = xy_bottom_from_bottom
        # Measure text height to position from bottom
        text_h = font_bottom.getbbox(text_bottom)[3] if hasattr(font_bottom, "getbbox") else font_bottom.getsize(text_bottom)[1]
        y_bottom = H - text_h - y_offset_bottom
        draw.text((x_bottom, y_bottom), text_bottom, font=font_bottom, fill=color_bottom)

    return Image.alpha_composite(base, overlay)


def main():
    parser = argparse.ArgumentParser(description="Add two text overlays to all PNGs in a folder.")
    parser.add_argument("folder", help="Relative path to the input folder containing PNG files.")
    args = parser.parse_args()

    in_dir = Path(args.folder)
    if not in_dir.exists() or not in_dir.is_dir():
        print(f'[error] "{in_dir}" is not a directory.')
        sys.exit(1)

    out_dir = in_dir.parent / f"{in_dir.name}-overlay"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Process PNGs alphabetically
    pngs = sorted([p for p in in_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"])
    total = len(pngs)
    if total == 0:
        print(f"[info] No PNG files found in {in_dir}")
        sys.exit(0)

    pad_width = len(str(total))
    font_top = load_font(FONT_PATH_TOP, FONT_SIZE_TOP)
    font_bottom = load_font(FONT_PATH_BOTTOM, FONT_SIZE_BOTTOM)

    for idx, src in enumerate(pngs, start=1):
        try:
            with Image.open(src) as im:
                # Replace backticks with zero-padded frame number
                frame_str = str(idx).zfill(pad_width)
                overlay_text_top = TEXT_LABEL_TOP.replace("`", frame_str)
                overlay_text_bottom = TEXT_LABEL_BOTTOM.replace("`", frame_str)

                result = add_text_overlays(
                    im,
                    overlay_text_top, (OFFSET_X_TOP, OFFSET_Y_TOP), font_top, FONT_COLOR_TOP,
                    overlay_text_bottom, (OFFSET_X_BOTTOM, OFFSET_Y_BOTTOM), font_bottom, FONT_COLOR_BOTTOM
                )

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
