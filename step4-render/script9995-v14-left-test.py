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
- Special leading "!":
    - If any label in any corner starts with "!", the "!" is removed,
      that label is rendered with a larger font (scaled by BIG),
      and subsequent labels are positioned based on the increased height.
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

# Scale factor for lines starting with "!"
BIG = 1.5  # e.g. 1.5x the base font size

# Time-related config
HOURS_PER_FRAME = 1.31   # now allowed to be a float   # this is for 0.9 timescale
# HOURS_PER_FRAME = 1.31 * (1 / 0.3)   # now allowed to be a float   # this is for 0.9 timescale
# HOURS_PER_FRAME = 0.98 #v11
TIME_LABEL_TEMPLATE = f"Time Estimate ({HOURS_PER_FRAME:.1f} hr/frame): X dd Y hr"

# --- Top-left overlay ---
TEXT_LABEL_TL = [
    "!ECDOsim v14 Test Render",
    # "Very Weak S1 -> S2",
    # f"Main Scenario: S1 -> S2",
    # "S1 -> S2, 2x Strength, Extended Drainage",
    # "S1 -> S2, Extended Drainage",
    # "Pivots: (0 S,121 E), (0 N,-59 W)"
    "Sahara Paleocurrent Formation Rendition"
]
OFFSET_X_TL = 15
OFFSET_Y_TL = 10
FONT_PATH_TL = "RobotoCondensed.ttf"
FONT_SIZE_TL = 10
FONT_SIZE_TL = 20
# FONT_SIZE_TL = 64
# FONT_SIZE_TL = 32
FONT_COLOR_TL = (0, 0, 0, 255)
FONT_COLOR_TL = (255, 255, 255, 255)

# --- Top-right overlay ---
TEXT_LABEL_TR = ["TIME", "Frame `/^"]
TEXT_LABEL_TR = ["Frame `/^"]
TEXT_LABEL_TR = []
OFFSET_X_TR = 15
OFFSET_Y_TR = 10
FONT_PATH_TR = "RobotoCondensed.ttf"
FONT_SIZE_TR = 14
FONT_SIZE_TR = 20
# FONT_SIZE_TR = 64
# FONT_SIZE_TR = 32
FONT_COLOR_TR = (0, 0, 0, 255)
FONT_COLOR_TR = (255, 255, 255, 255)

# --- Bottom-left overlay ---
TEXT_LABEL_BL = [
    "Video: 1080x1080 pixels",
    # "Terrain: 50"
    "Fluid: 3 million particles"
    # "~12 million particles"
]
# TEXT_LABEL_BL = []
OFFSET_X_BL = 15
OFFSET_Y_BL = 10
FONT_PATH_BL = "RobotoCondensed.ttf"
FONT_SIZE_BL = 13
FONT_SIZE_BL = 26
# FONT_SIZE_BL = 50
# FONT_SIZE_BL = 26
FONT_COLOR_BL = (0, 0, 0, 255)
FONT_COLOR_BL = (255, 255, 255, 255)

# --- Bottom-right overlay ---
TEXT_LABEL_BR = [
    "By Junho (Dec. 2025)",
    "@ sovrynn.github.io",
]
TEXT_LABEL_BR = []
OFFSET_X_BR = 15
OFFSET_Y_BR = 10
FONT_PATH_BR = "RobotoCondensed.ttf"
FONT_SIZE_BR = 13
FONT_SIZE_BR = 26
# FONT_SIZE_BR = 50
# FONT_SIZE_BR = 26
FONT_COLOR_BR = (0, 0, 0, 255)
FONT_COLOR_BR = (255, 255, 255, 255)

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
    """
    Each of tl/tr/bl/br is either None or a dict with:
      - "lines": list of {"text": str, "big": bool}
      - "font": base font
      - "font_big": font for big lines
      - "color": RGBA tuple
      - "offset_x", "offset_y": ints
    """
    if img.mode != "RGBA":
        base = img.convert("RGBA")
    else:
        base = img.copy()

    W, H = base.size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # ---------- Top-left ----------
    if tl and tl.get("lines"):
        x = tl["offset_x"]
        y = tl["offset_y"]
        for item in tl["lines"]:
            text = item["text"]
            font = tl["font_big"] if item.get("big") else tl["font"]
            lh = _line_height(font)
            draw.text((x, y), text, font=font, fill=tl["color"])
            y += lh + line_spacing

    # ---------- Top-right ----------
    if tr and tr.get("lines"):
        y = tr["offset_y"]
        for item in tr["lines"]:
            text = item["text"]
            font = tr["font_big"] if item.get("big") else tr["font"]
            tw, _ = _text_size(font, text)
            x = W - tw - tr["offset_x"]
            lh = _line_height(font)
            draw.text((x, y), text, font=font, fill=tr["color"])
            y += lh + line_spacing

    # ---------- Bottom-left ----------
    if bl and bl.get("lines"):
        # compute total height with per-line fonts
        total_h = 0
        for i, item in enumerate(bl["lines"]):
            font = bl["font_big"] if item.get("big") else bl["font"]
            lh = _line_height(font)
            total_h += lh
            if i < len(bl["lines"]) - 1:
                total_h += line_spacing

        x = bl["offset_x"]
        y = H - bl["offset_y"] - total_h
        for item in bl["lines"]:
            text = item["text"]
            font = bl["font_big"] if item.get("big") else bl["font"]
            lh = _line_height(font)
            draw.text((x, y), text, font=font, fill=bl["color"])
            y += lh + line_spacing

    # ---------- Bottom-right ----------
    if br and br.get("lines"):
        # compute total height with per-line fonts
        total_h = 0
        for i, item in enumerate(br["lines"]):
            font = br["font_big"] if item.get("big") else br["font"]
            lh = _line_height(font)
            total_h += lh
            if i < len(br["lines"]) - 1:
                total_h += line_spacing

        y = H - br["offset_y"] - total_h
        for item in br["lines"]:
            text = item["text"]
            font = br["font_big"] if item.get("big") else br["font"]
            tw, _ = _text_size(font, text)
            x = W - tw - br["offset_x"]
            lh = _line_height(font)
            draw.text((x, y), text, font=font, fill=br["color"])
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

    # base fonts
    font_tl = load_font(FONT_PATH_TL, FONT_SIZE_TL)
    font_tr = load_font(FONT_PATH_TR, FONT_SIZE_TR)
    font_bl = load_font(FONT_PATH_BL, FONT_SIZE_BL)
    font_br = load_font(FONT_PATH_BR, FONT_SIZE_BR)

    # big fonts for lines starting with "!"
    font_tl_big = load_font(FONT_PATH_TL, int(round(FONT_SIZE_TL * BIG)))
    font_tr_big = load_font(FONT_PATH_TR, int(round(FONT_SIZE_TR * BIG)))
    font_bl_big = load_font(FONT_PATH_BL, int(round(FONT_SIZE_BL * BIG)))
    font_br_big = load_font(FONT_PATH_BR, int(round(FONT_SIZE_BR * BIG)))

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
                    """
                    Returns list of dicts:
                      {"text": str, "big": bool}
                    """
                    out = []
                    for t in _normalize_texts(label):
                        is_big = t.startswith("!")
                        if is_big:
                            # remove leading "!" and optional following space
                            t = t[1:].lstrip()

                        if t == "TIME":
                            text_val = build_time_label(idx, pad_days, pad_hours)
                        else:
                            text_val = replace_tokens(t)

                        out.append({"text": text_val, "big": is_big})
                    return out

                tl_lines = process_label(TEXT_LABEL_TL)
                tr_lines = process_label(TEXT_LABEL_TR)
                bl_lines = process_label(TEXT_LABEL_BL)
                br_lines = process_label(TEXT_LABEL_BR)

                result = add_text_overlays(
                    im,
                    tl={
                        "lines": tl_lines,
                        "font": font_tl,
                        "font_big": font_tl_big,
                        "color": FONT_COLOR_TL,
                        "offset_x": OFFSET_X_TL,
                        "offset_y": OFFSET_Y_TL,
                    },
                    tr={
                        "lines": tr_lines,
                        "font": font_tr,
                        "font_big": font_tr_big,
                        "color": FONT_COLOR_TR,
                        "offset_x": OFFSET_X_TR,
                        "offset_y": OFFSET_Y_TR,
                    },
                    bl={
                        "lines": bl_lines,
                        "font": font_bl,
                        "font_big": font_bl_big,
                        "color": FONT_COLOR_BL,
                        "offset_x": OFFSET_X_BL,
                        "offset_y": OFFSET_Y_BL,
                    },
                    br={
                        "lines": br_lines,
                        "font": font_br,
                        "font_big": font_br_big,
                        "color": FONT_COLOR_BR,
                        "offset_x": OFFSET_X_BR,
                        "offset_y": OFFSET_Y_BR,
                    },
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
