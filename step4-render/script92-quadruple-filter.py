#!/usr/bin/env python3
"""
Batch text overlay for PNGs in a relative folder.

Usage:
  python add_overlay.py path/to/relative/folder

Writes processed images to "<folder>-overlay" next to the input folder.

Notes:
- Each corner overlay has its own text, font, size, color, and offsets.
- Replace backticks ` in any TEXT_LABEL_* with the alphabetical 1-based index
  of the file among *all* PNGs in the folder (not the FILTER index).
- Replace caret ^ in any TEXT_LABEL_* with the total number of PNGs in the folder.
- The FILTER list (defined below) limits which PNGs are processed.
"""

from pathlib import Path
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont

# =========================
# Config — edit these
# =========================
# --- Top-left overlay ---
TEXT_LABEL_TL = "ECDOsim v10 (Main Scenario: S1 -> S2)"
OFFSET_X_TL = 15
OFFSET_Y_TL = 10
FONT_PATH_TL = "RobotoCondensed.ttf"
FONT_SIZE_TL = 32
FONT_COLOR_TL = (0, 0, 0, 255)

# --- Top-right overlay ---
TEXT_LABEL_TR = "Frame `/^"
OFFSET_X_TR = 15
OFFSET_Y_TR = 10
FONT_PATH_TR = "RobotoCondensed.ttf"
FONT_SIZE_TR = 32
FONT_COLOR_TR = (0, 0, 0, 255)

# --- Bottom-left overlay ---
TEXT_LABEL_BL = "~19 mm particles (~68 km³), Pivots: (-20 S,130 E), (20 N,-50 W)"
OFFSET_X_BL = 15
OFFSET_Y_BL = 10
FONT_PATH_BL = "RobotoCondensed.ttf"
FONT_SIZE_BL = 26
FONT_COLOR_BL = (0, 0, 0, 255)

# --- Bottom-right overlay ---
TEXT_LABEL_BR = "By Junho (Nov. 2025) @ sovrynn.github.io"
OFFSET_X_BR = 15
OFFSET_Y_BR = 10
FONT_PATH_BR = "RobotoCondensed.ttf"
FONT_SIZE_BR = 26
FONT_COLOR_BR = (0, 0, 0, 255)

# --- Filter: only process these filenames (with extensions) ---
# Leave empty ([]) to process all PNGs in the input folder.
FILTER = ["0172.png","0175.png"]  # e.g., ["frame001.png", "frame005.png"]
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
    else:
        return font.getsize(text)


def add_text_overlays(img, tl, tr, bl, br):
    """Draw four text overlays (top-left, top-right, bottom-left, bottom-right)."""
    if img.mode != "RGBA":
        base = img.convert("RGBA")
    else:
        base = img.copy()

    W, H = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # --- Top-left ---
    if tl and tl.get("text"):
        draw.text((tl["offset_x"], tl["offset_y"]),
                  tl["text"], font=tl["font"], fill=tl["color"])

    # --- Top-right ---
    if tr and tr.get("text"):
        text_w, text_h = _text_size(tr["font"], tr["text"])
        x = W - text_w - tr["offset_x"]
        y = tr["offset_y"]
        draw.text((x, y), tr["text"], font=tr["font"], fill=tr["color"])

    # --- Bottom-left ---
    if bl and bl.get("text"):
        text_w, text_h = _text_size(bl["font"], bl["text"])
        x = bl["offset_x"]
        y = H - text_h - bl["offset_y"]
        draw.text((x, y), bl["text"], font=bl["font"], fill=bl["color"])

    # --- Bottom-right ---
    if br and br.get("text"):
        text_w, text_h = _text_size(br["font"], br["text"])
        x = W - text_w - br["offset_x"]
        y = H - text_h - br["offset_y"]
        draw.text((x, y), br["text"], font=br["font"], fill=br["color"])

    return Image.alpha_composite(base, overlay)


def main():
    parser = argparse.ArgumentParser(
        description="Add four corner text overlays to all PNGs in a folder."
    )
    parser.add_argument(
        "folder",
        help="Relative path to the input folder containing PNG files."
    )
    args = parser.parse_args()

    in_dir = Path(args.folder)
    if not in_dir.exists() or not in_dir.is_dir():
        print(f'[error] "{in_dir}" is not a directory.')
        sys.exit(1)

    out_dir = in_dir.parent / f"{in_dir.name}-overlay"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Gather all PNGs (alphabetical order baseline)
    all_pngs = sorted([p for p in in_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"])
    total_pngs_in_folder = len(all_pngs)

    if total_pngs_in_folder == 0:
        print(f"[info] No PNG files found in {in_dir}")
        sys.exit(0)

    # Map filename -> alphabetical 1-based position among ALL PNGs in folder
    alpha_index = {p.name: i for i, p in enumerate(all_pngs, start=1)}

    # Apply FILTER to choose which to process
    if FILTER:
        requested = set(FILTER)
        by_name = {p.name: p for p in all_pngs}
        pngs = [by_name[name] for name in requested if name in by_name]

        missing = [name for name in requested if name not in by_name]
        if missing:
            print(f"[warn] These requested files were not found: {', '.join(missing)}")
    else:
        pngs = all_pngs

    total_to_process = len(pngs)
    if total_to_process == 0:
        print(f"[info] No matching PNG files to process in {in_dir} for the FILTER list.")
        sys.exit(0)

    # Pad width based on the maximum alphabetical index (i.e., total PNGs in folder)
    pad_width = len(str(total_pngs_in_folder))

    font_tl = load_font(FONT_PATH_TL, FONT_SIZE_TL)
    font_tr = load_font(FONT_PATH_TR, FONT_SIZE_TR)
    font_bl = load_font(FONT_PATH_BL, FONT_SIZE_BL)
    font_br = load_font(FONT_PATH_BR, FONT_SIZE_BR)

    for idx, src in enumerate(pngs, start=1):
        try:
            with Image.open(src) as im:
                # Alphabetical index among ALL PNGs in folder (1-based)
                alpha_pos = alpha_index.get(src.name, idx)
                frame_str = str(alpha_pos).zfill(pad_width)

                def replace_tokens(text: str) -> str:
                    """Replace ` with alphabetical index; ^ with total PNG count in folder."""
                    return text.replace("`", frame_str).replace("^", str(total_pngs_in_folder))

                tl_text = replace_tokens(TEXT_LABEL_TL) if TEXT_LABEL_TL else ""
                tr_text = replace_tokens(TEXT_LABEL_TR) if TEXT_LABEL_TR else ""
                bl_text = replace_tokens(TEXT_LABEL_BL) if TEXT_LABEL_BL else ""
                br_text = replace_tokens(TEXT_LABEL_BR) if TEXT_LABEL_BR else ""

                result = add_text_overlays(
                    im,
                    tl={"text": tl_text, "font": font_tl, "color": FONT_COLOR_TL,
                        "offset_x": OFFSET_X_TL, "offset_y": OFFSET_Y_TL},
                    tr={"text": tr_text, "font": font_tr, "color": FONT_COLOR_TR,
                        "offset_x": OFFSET_X_TR, "offset_y": OFFSET_Y_TR},
                    bl={"text": bl_text, "font": font_bl, "color": FONT_COLOR_BL,
                        "offset_x": OFFSET_X_BL, "offset_y": OFFSET_Y_BL},
                    br={"text": br_text, "font": font_br, "color": FONT_COLOR_BR,
                        "offset_x": OFFSET_X_BR, "offset_y": OFFSET_Y_BR},
                )

                save_kwargs = {}
                if "dpi" in im.info:
                    save_kwargs["dpi"] = im.info["dpi"]

                dst = out_dir / src.name
                result.save(dst, format="PNG", **save_kwargs)

            rel = dst.relative_to(Path.cwd()) if dst.is_absolute() else dst
            print(f"[{idx}/{total_to_process}] {src.name} -> {rel}")
        except Exception as e:
            print(f"[error] Failed on {src.name}: {e}")

    print(f"[done] Wrote {total_to_process} file(s) to {out_dir}")


if __name__ == "__main__":
    main()
