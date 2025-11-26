#!/usr/bin/env python3
import sys
import os
import numpy as np
import rasterio

def main():
    if len(sys.argv) != 3:
        print("Usage: python gray_scale_single_band.py <relative_path_to_tif> <scale>")
        sys.exit(1)

    in_path = sys.argv[1]
    try:
        scale = float(sys.argv[2])
    except ValueError:
        print("Error: <scale> must be a number.")
        sys.exit(1)

    if not os.path.exists(in_path):
        print(f"Error: file not found: {in_path}")
        sys.exit(1)

    with rasterio.open(in_path) as src:
        if src.count < 3:
            print("Error: input must have at least 3 bands (RGB).")
            sys.exit(1)

        # Take just one RGB band (since the image is grayscale replicated across RGB)
        r = src.read(1).astype(np.float32)

        # Normalize to 0..1 by dividing by 255 and invert so white → 0, black → 1
        gray01 = 1 - (r / 255.0)

        # Apply scale
        out = gray01 * scale
        # Uncomment below if you want to clip the values
        # out = np.clip(out, 0.0, 1.0)

        # Prepare output profile: single band, float32 to preserve 0..scale values
        profile = src.profile.copy()
        profile.update(
            count=1,
            dtype="float32",
        )
        profile.pop("photometric", None)

        # Output path in the same directory as the input file
        in_dir = os.path.dirname(os.path.abspath(in_path))
        base, ext = os.path.splitext(os.path.basename(in_path))
        out_path = os.path.join(in_dir, f"{base}_x{sys.argv[2]}pScaled_float32{ext}")

        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(out, 1)

    print(f"✅ Wrote single-band scaled grayscale to: {out_path}")
    print(f"   Value range ~ [{float(out.min()):.6f}, {float(out.max()):.6f}]")

if __name__ == "__main__":
    main()
