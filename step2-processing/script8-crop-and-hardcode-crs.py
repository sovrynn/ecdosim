#!/usr/bin/env python3
import sys
import os
import numpy as np
import rasterio
from rasterio.windows import Window

def parse_ratio(x, name):
    try:
        v = float(x)
    except ValueError:
        raise ValueError(f"{name} must be a number between 0 and 1.")
    if not (0.0 <= v <= 1.0):
        raise ValueError(f"{name} must be between 0 and 1 (got {v}).")
    return v

def main():
    if len(sys.argv) != 6:
        print("Usage: python crop_and_retag_crs.py <relative_path_to_tif> <left> <top> <right> <bottom>")
        sys.exit(1)

    in_path = sys.argv[1]
    if not os.path.exists(in_path):
        print(f"Error: file not found: {in_path}")
        sys.exit(1)

    # Ratios: left, top, right, bottom ∈ [0,1]
    l = parse_ratio(sys.argv[2], "left")
    t = parse_ratio(sys.argv[3], "top")
    r = parse_ratio(sys.argv[4], "right")
    b = parse_ratio(sys.argv[5], "bottom")

    # Open input
    with rasterio.open(in_path) as src:
        height, width = src.height, src.width

        # Compute pixel counts to remove (floor via int())
        left_cols   = int(width  * l)
        right_cols  = int(width  * r)
        top_rows    = int(height * t)
        bottom_rows = int(height * b)

        # Validate remaining size
        new_w = width  - (left_cols + right_cols)
        new_h = height - (top_rows + bottom_rows)
        if new_w <= 0 or new_h <= 0:
            print(
                "Error: cropping ratios remove all pixels in width and/or height. "
                f"Requested new size would be {new_w}x{new_h}."
            )
            sys.exit(1)

        # Define window (col_off, row_off, width, height)
        win = Window(
            col_off=left_cols,
            row_off=top_rows,
            width=new_w,
            height=new_h
        )

        # Read only the window for all bands
        data = src.read(window=win)

        # Prepare output profile:
        #  - Update width/height
        #  - IMPORTANT: per request, DO NOT reproject or modify raster values;
        #    we simply change the CRS header to EPSG:4326 (WGS84) and keep the
        #    transform exactly as-is (i.e., not adjusted for the crop).
        profile = src.profile.copy()
        profile.update(
            width=new_w,
            height=new_h,
            crs="EPSG:4326"  # Change only the CRS header
            # Note: leaving 'transform' unchanged intentionally
        )

    # Build output path next to the input file
    in_dir  = os.path.dirname(os.path.abspath(in_path))
    base, ext = os.path.splitext(os.path.basename(in_path))
    # Make short tokens for ratios (e.g., 0.25 -> 025)
    def tok(v): return f"{int(round(v*100)):03d}"
    out_name = f"{base}_crop_L{tok(l)}_T{tok(t)}_R{tok(r)}_B{tok(b)}_crs4326{ext}"
    out_path = os.path.join(in_dir, out_name)

    # Write output
    with rasterio.open(out_path, "w", **profile) as dst:
        dst.write(data)

    print(f"✅ Wrote: {out_path}")
    print(f"   Size: {new_w} x {new_h}")
    print("   Note: CRS header set to EPSG:4326 WITHOUT reprojection or transform changes.")

if __name__ == "__main__":
    main()
