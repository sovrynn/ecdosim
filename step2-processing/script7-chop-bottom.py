#!/usr/bin/env python3
import sys
import argparse
import numpy as np
import rasterio
import os

def main():
    parser = argparse.ArgumentParser(
        description="Clamp all grayscale values below THRESHOLD up to THRESHOLD for a single-band TIFF."
    )
    parser.add_argument("tif_path", help="Relative or absolute path to the input TIFF")
    parser.add_argument(
        "--threshold", "-t",
        type=float, required=True,
        help="Threshold value: any pixel below this becomes this value"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Optional: specify output TIFF path (default: same directory as input, named *_clamped.tif)"
    )
    args = parser.parse_args()

    # Determine output path
    input_dir = os.path.dirname(os.path.abspath(args.tif_path))
    input_base = os.path.splitext(os.path.basename(args.tif_path))[0]
    if args.output is None:
        output_path = os.path.join(input_dir, f"{input_base}_clamped.tif")
    else:
        output_path = args.output

    # Open source
    with rasterio.open(args.tif_path) as src:
        if src.count != 1:
            print(f"Error: Expected a single-band TIFF, but found {src.count} bands.")
            sys.exit(2)

        # Read as masked array to preserve NoData
        band = src.read(1, masked=True)
        nodata = src.nodata
        profile = src.profile.copy()
        dtype = src.dtypes[0]
        total_pixels = src.width * src.height  # includes NoData cells

        # Prepare threshold value in the band dtype
        np_dtype = np.dtype(dtype)
        thr = args.threshold
        if np.issubdtype(np_dtype, np.integer):
            info = np.iinfo(np_dtype)
            thr = max(info.min, min(info.max, int(round(thr))))
        else:
            thr = np_dtype.type(thr)

        # Compute mask of valid data and which pixels will be replaced
        valid_mask = ~band.mask if np.ma.isMaskedArray(band) else np.ones_like(band, dtype=bool)
        replace_mask = valid_mask & (band.data < thr)

        # Apply replacement (preserving mask)
        replaced_data = band.data.copy()
        replaced_data[replace_mask] = thr
        replaced = np.ma.array(replaced_data, mask=band.mask, dtype=np_dtype)

        # Count replaced
        replaced_count = int(np.count_nonzero(replace_mask))
        replaced_percent = (replaced_count / total_pixels * 100.0) if total_pixels > 0 else 0.0

        # Write output (fill masked cells with nodata if defined, else with 0)
        profile.update(count=1, dtype=dtype)
        fill_value = nodata if nodata is not None else np_dtype.type(0)
        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(replaced.filled(fill_value), 1)

        # Report
        print(f"Input: {args.tif_path}")
        print(f"Output: {output_path}")
        print(f"Threshold: {thr} (applied to pixels < threshold)")
        print(f"Total pixels: {total_pixels}")
        print(f"Pixels replaced: {replaced_count} ({replaced_percent:.4f}%)")

if __name__ == "__main__":
    main()
