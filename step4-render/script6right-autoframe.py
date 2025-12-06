#!/usr/bin/env python3
"""
Batch text overlay for PNGs in a relative folder.

Usage:
  python add_overlay.py path/to/relative/folder

Writes processed images to "<folder>-overlay" next to the input folder.

Markers in any TEXT_LABEL_*:
  `  -> current frame number (zero-padded to total digits)
  ~  -> total number of frames in the folder
"""

from pathlib import Path
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont

# =========================
# Config — edit these
# =========================
# --- Top-left overlay ---
TEXT_LABEL_TL = ""
OFFSET_X_TL = 15          # distance from left
OFFSET_Y_TL = 10          # distance from top
FONT_PATH_TL = "RobotoCondensed.ttf"
FONT_SIZE_TL = 32
FONT_COLOR_TL = (0, 0, 0, 255)

# --- Top-right overlay ---
TEXT_LABEL_TR = "Frame `/;"
OFFSET_X_TR = 15          # distance from right
OFFSET_Y_TR = 10          # distance from top
FONT_PATH_TR = "RobotoCondensed.ttf"
FONT_SIZE_TR = 32
FONT_COLOR_TR = (0, 0, 0, 255)

# --- Bottom-left overlay ---
TEXT_LABEL_BL = ""
OFFSET_X_BL = 15          # distance from left
OFFSET_Y_BL = 10          # distance from bottom
FONT_PATH_BL = "RobotoCondensed.ttf"
FONT_SIZE_BL = 26
FONT_COLOR_BL = (0, 0, 0, 255)

# --- Bottom-right overlay ---
TEXT_LABEL_BR = "By Junho (Nov. 2025) @ sovrynn.github.io"
OFFSET_X_BR = 15          # distance from right
OFFSET_Y_BR = 10          # distance from bottom
FONT_PATH_BR = "RobotoCondensed.ttf"
FONT_SIZE_BR = 26
FONT_COLOR_BR = (0, 0, 0, 255)
# =========================


def load_font(font_path: str, size: int):
    """Try loading the specified font, fallback to default if unavailable."""
    try:
        return ImageFont.truetype(font_path, size=size)
    except Exception:
        print(f"[warn] Could not load font '{font_path}'; using default font.")
        return ImageFont.load_default()


def _text_size(font: ImageFont.ImageFont, text: str):
    """Return (width, height) of rendered text with the given font."""
    if hasattr(font, "getbbox"):
        x0, y0, x1, y1 = font.getbbox(text)
        return (x1 - x0, y1 - y0)
    return font.getsize(text)


def add_text_overlays(img, tl, tr, bl, br):
    """
    Draw four text overlays (top-left, top-right, bottom-left, bottom-right).
    Each of tl/tr/bl/br is a dict with keys: text, font, color, offset_x, offset_y
    """
    base = img.convert("RGBA") if img.mode != "RGBA" else img.copy()
    W, H = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Top-left
    if tl and tl.get("text"):
        draw.text((tl["offset_x"], tl["offset_y"]),
                  tl["text"], font=tl["font"], fill=tl["color"])

    # Top-right
    if tr and tr.get("text"):
        tw, th = _text_size(tr["font"], tr["text"])
        draw.text((W - tw - tr["offset_x"], tr["offset_y"]),
                  tr["text"], font=tr["font"], fill=tr["color"])

    # Bottom-left
    if bl and bl.get("text"):
        tw, th = _text_size(bl["font"], bl["text"])
        draw.text((bl["offset_x"], H - th - bl["offset_y"]),
                  bl["text"], font=bl["font"], fill=bl["color"])

    # Bottom-right
    if br and br.get("text"):
        tw, th = _text_size(br["font"], br["text"])
        draw.text((W - tw - br["offset_x"], H - th - br["offset_y"]),
                  br["text"], font=br["font"], fill=br["color"])

    return Image.alpha_composite(base, overlay)


def replace_markers(s: str, frame_str: str, total_str: str) -> str:
    """
    Replace special markers in overlay strings:
      ` -> frame number string (already zero-padded)
      ~ -> total frames string
    """
    if not s:
        return s
    return s.replace("`", frame_str).replace(";", total_str)


def main():
    parser = argparse.ArgumentParser(description="Add four corner text overlays to all PNGs in a folder.")
    parser.add_argument("folder", help="Relative path to the input folder containing PNG files.")
    args = parser.parse_args()

    in_dir = Path(args.folder)
    if not in_dir.exists() or not in_dir.is_dir():
        print(f'[error] "{in_dir}" is not a directory.')
        sys.exit(1)

    out_dir = in_dir.parent / f"{in_dir.name}-overlay"
    out_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted([p for p in in_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"])
    total = len(pngs)
    if total == 0:
        print(f"[info] No PNG files found in {in_dir}")
        sys.exit(0)

    pad_width = len(str(total))      # zero-pad frames to same digit width as total
    total_str = str(total)

    # Load fonts
    font_tl = load_font(FONT_PATH_TL, FONT_SIZE_TL)
    font_tr = load_font(FONT_PATH_TR, FONT_SIZE_TR)
    font_bl = load_font(FONT_PATH_BL, FONT_SIZE_BL)
    font_br = load_font(FONT_PATH_BR, FONT_SIZE_BR)

    for idx, src in enumerate(pngs, start=1):
        try:
            with Image.open(src) as im:
                frame_str = str(idx).zfill(pad_width)

                tl_text = replace_markers(TEXT_LABEL_TL, frame_str, total_str)
                tr_text = replace_markers(TEXT_LABEL_TR, frame_str, total_str)
                bl_text = replace_markers(TEXT_LABEL_BL, frame_str, total_str)
                br_text = replace_markers(TEXT_LABEL_BR, frame_str, total_str)

                result = add_text_overlays(
                    im,
                    tl={"text": tl_text, "font": font_tl, "color": FONT_COLOR_TL, "offset_x": OFFSET_X_TL, "offset_y": OFFSET_Y_TL},
                    tr={"text": tr_text, "font": font_tr, "color": FONT_COLOR_TR, "offset_x": OFFSET_X_TR, "offset_y": OFFSET_Y_TR},
                    bl={"text": bl_text, "font": font_bl, "color": FONT_COLOR_BL, "offset_x": OFFSET_X_BL, "offset_y": OFFSET_Y_BL},
                    br={"text": br_text, "font": font_br, "color": FONT_COLOR_BR, "offset_x": OFFSET_X_BR, "offset_y": OFFSET_Y_BR},
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
