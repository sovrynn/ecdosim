#!/usr/bin/env python3
"""
Batch text overlay for PNGs in a relative folder.

Usage:
  python add_overlay.py path/to/relative/folder

Writes processed images to "<folder>-overlay" next to the input folder.

Notes:
- Each corner overlay has its own text, font, size, color, and offsets.
- Replace backticks ` in any TEXT_LABEL_* with the zero-padded frame number.
- Replace caret ^ in any TEXT_LABEL_* with the total number of frames.
- TEXT_LABEL_* may be either a single string or a list of strings.
- Special label value "TIME":
    - If a corner's label list contains the string "TIME", that entry is replaced
      for each frame with TIME_LABEL_TEMPLATE where:
        X = zero-padded days
        Y = zero-padded hours
      computed from HOURS_PER_FRAME (float allowed).
"""

from pathlib import Path
import sys
import argparse
import math
from PIL import Image, ImageDraw, ImageFont

# =========================
# Config — edit these
# =========================

LINE_SPACING = 1

# Time-related config
HOURS_PER_FRAME = 1.31   # now allowed to be a float
TIME_LABEL_TEMPLATE = f"Estimate ({HOURS_PER_FRAME:.1f} hr/frame): X dd Y hr"

# --- Top-left overlay ---
TEXT_LABEL_TL = [
    "ECDOsim v10 Bonus Scenario:",
    # "S1 -> S2, 2x Strength, Extended Drainage",
    "S1 -> S2, Extended Drainage",
    "Pivots: (-20 S,130 E), (20 N,-50 W)"
]
OFFSET_X_TL = 15
OFFSET_Y_TL = 10
FONT_PATH_TL = "RobotoCondensed.ttf"
FONT_SIZE_TL = 10
FONT_COLOR_TL = (0, 0, 0, 255)

# --- Top-right overlay ---
TEXT_LABEL_TR = [] #["TIME", "Frame `/^"]
OFFSET_X_TR = 15
OFFSET_Y_TR = 10
FONT_PATH_TR = "RobotoCondensed.ttf"
FONT_SIZE_TR = 14
FONT_COLOR_TR = (0, 0, 0, 255)

# --- Bottom-left overlay ---
TEXT_LABEL_BL = [
    "720x720 pixels",
    # "~12 million particles"
    "~8 million particles"
]
OFFSET_X_BL = 15
OFFSET_Y_BL = 10
FONT_PATH_BL = "RobotoCondensed.ttf"
FONT_SIZE_BL = 13
FONT_COLOR_BL = (0, 0, 0, 255)

# --- Bottom-right overlay ---
TEXT_LABEL_BR = []
# [
#     "By Junho (Nov. 2025)",
#     "@ sovrynn.github.io",
# ]
OFFSET_X_BR = 15
OFFSET_Y_BR = 10
FONT_PATH_BR = "RobotoCondensed.ttf"
FONT_SIZE_BR = 13
FONT_COLOR_BR = (0, 0, 0, 255)

# ===========================================================

def load_font(font_path: str, size: int):
    try:
        return ImageFont.truetype(font_path, size=size)
    except Exception:
        print(f"[warn] Could not load font '{font_path}'; using default font.")
        return ImageFont.load_default()

def _text_size(font, text):
    if hasattr(font, "getbbox"):
        x0, y0, x1, y1 = font.getbbox(text)
        return (x1 - x0, y1 - y0)
    return font.getsize(text)

def _line_height(font):
    if hasattr(font, "getmetrics"):
        a, d = font.getmetrics()
        return a + d
    _, h = _text_size(font, "Mg")
    return h

def _normalize_texts(label):
    if label is None:
        return []
    if isinstance(label, str):
        s = label.strip()
        return [s] if s else []
    try:
        out = []
        for item in label:
            if item is None:
                continue
            s = str(item).strip()
            if s:
                out.append(s)
        return out
    except TypeError:
        s = str(label).strip()
        return [s] if s else []

def build_time_label(frame_index: int, pad_days: int, pad_hours: int) -> str:
    """
    Compute elapsed hours as float and round *only for display*.
    Never overwrite float values.
    """
    elapsed_hours_float = (frame_index - 1) * HOURS_PER_FRAME
    elapsed_hours_display = int(round(elapsed_hours_float))

    days = elapsed_hours_display // 24
    hours = elapsed_hours_display % 24

    day_str = str(days).zfill(pad_days)
    hour_str = str(hours).zfill(pad_hours)

    return TIME_LABEL_TEMPLATE.replace("X", day_str).replace("Y", hour_str)

def add_text_overlays(img, tl, tr, bl, br, line_spacing=0):
    if img.mode != "RGBA":
        base = img.convert("RGBA")
    else:
        base = img.copy()

    W, H = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # TL
    if tl and tl.get("texts"):
        lh = _line_height(tl["font"])
        x = tl["offset_x"]
        y = tl["offset_y"]
        for line in tl["texts"]:
            draw.text((x, y), line, font=tl["font"], fill=tl["color"])
            y += lh + line_spacing

    # TR
    if tr and tr.get("texts"):
        lh = _line_height(tr["font"])
        y = tr["offset_y"]
        for line in tr["texts"]:
            tw, _ = _text_size(tr["font"], line)
            x = W - tw - tr["offset_x"]
            draw.text((x, y), line, font=tr["font"], fill=tr["color"])
            y += lh + line_spacing

    # BL
    if bl and bl.get("texts"):
        lh = _line_height(bl["font"])
        n = len(bl["texts"])
        total_h = n * lh + line_spacing * (n - 1)
        x = bl["offset_x"]
        y = H - bl["offset_y"] - total_h
        for line in bl["texts"]:
            draw.text((x, y), line, font=bl["font"], fill=bl["color"])
            y += lh + line_spacing

    # BR
    if br and br.get("texts"):
        lh = _line_height(br["font"])
        n = len(br["texts"])
        total_h = n * lh + line_spacing * (n - 1)
        y = H - br["offset_y"] - total_h
        for line in br["texts"]:
            tw, _ = _text_size(br["font"], line)
            x = W - tw - br["offset_x"]
            draw.text((x, y), line, font=br["font"], fill=br["color"])
            y += lh + line_spacing

    return Image.alpha_composite(base, overlay)

def main():
    parser = argparse.ArgumentParser(description="Add corner overlays to PNGs in a folder.")
    parser.add_argument("folder")
    args = parser.parse_args()

    in_dir = Path(args.folder)
    if not in_dir.exists() or not in_dir.is_dir():
        print(f'[error] "{in_dir}" is not a directory.')
        sys.exit(1)

    out_dir = in_dir.parent / f"{in_dir.name}-overlay"
    out_dir.mkdir(parents=True, exist_ok=True)

    pngs = sorted([p for p in in_dir.iterdir() if p.suffix.lower() == ".png"])
    total = len(pngs)
    if total == 0:
        print(f"[info] No PNGs found.")
        sys.exit(0)

    pad_width = len(str(total))

    font_tl = load_font(FONT_PATH_TL, FONT_SIZE_TL)
    font_tr = load_font(FONT_PATH_TR, FONT_SIZE_TR)
    font_bl = load_font(FONT_PATH_BL, FONT_SIZE_BL)
    font_br = load_font(FONT_PATH_BR, FONT_SIZE_BR)

    # Compute padding based on *display-rounded* max time
    max_elapsed_hours_float = (total - 1) * HOURS_PER_FRAME
    max_elapsed_hours_display = int(round(max_elapsed_hours_float))
    max_days = max_elapsed_hours_display // 24
    max_hours = max_elapsed_hours_display % 24
    pad_days = max(len(str(max_days)), 1)
    pad_hours = max(len(str(max_hours)), 1)
    pad_hours = 2

    for idx, src in enumerate(pngs, 1):
        try:
            with Image.open(src) as im:
                frame_str = str(idx).zfill(pad_width)

                def replace_tokens(s):
                    return s.replace("`", frame_str).replace("^", str(total))

                def process_label(label):
                    out = []
                    for t in _normalize_texts(label):
                        if t == "TIME":
                            out.append(build_time_label(idx, pad_days, pad_hours))
                        else:
                            out.append(replace_tokens(t))
                    return out

                tl_texts = process_label(TEXT_LABEL_TL)
                tr_texts = process_label(TEXT_LABEL_TR)
                bl_texts = process_label(TEXT_LABEL_BL)
                br_texts = process_label(TEXT_LABEL_BR)

                result = add_text_overlays(
                    im,
                    tl={"texts": tl_texts, "font": font_tl, "color": FONT_COLOR_TL,
                        "offset_x": OFFSET_X_TL, "offset_y": OFFSET_Y_TL},
                    tr={"texts": tr_texts, "font": font_tr, "color": FONT_COLOR_TR,
                        "offset_x": OFFSET_X_TR, "offset_y": OFFSET_Y_TR},
                    bl={"texts": bl_texts, "font": font_bl, "color": FONT_COLOR_BL,
                        "offset_x": OFFSET_X_BL, "offset_y": OFFSET_Y_BL},
                    br={"texts": br_texts, "font": font_br, "color": FONT_COLOR_BR,
                        "offset_x": OFFSET_X_BR, "offset_y": OFFSET_Y_BR},
                    line_spacing=LINE_SPACING,
                )

                save_kwargs = {}
                if "dpi" in im.info:
                    save_kwargs["dpi"] = im.info["dpi"]

                dst = out_dir / src.name
                result.save(dst, format="PNG", **save_kwargs)

            print(f"[{idx}/{total}] {src.name} -> {dst}")

        except Exception as e:
            print(f"[error] Failed on {src.name}: {e}")

    print(f"[done] Wrote {total} files to {out_dir}")

if __name__ == "__main__":
    main()
