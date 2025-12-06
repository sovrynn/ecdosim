#!/usr/bin/env python3

import argparse
from pathlib import Path

import numpy as np
import rasterio


def compute_circle_mask(height, width):
    """
    Create a boolean mask for a circle centered in the image,
    touching the closest border, fully contained in the image.
    """
    # Center in pixel coordinates (col, row)
    cx = (width - 1) / 2.0
    cy = (height - 1) / 2.0

    # Distance from center to each border (in pixels)
    dist_left = cx
    dist_right = (width - 1) - cx
    dist_top = cy
    dist_bottom = (height - 1) - cy

    radius = min(dist_left, dist_right, dist_top, dist_bottom)

    # Create grid of coordinates
    y_indices, x_indices = np.ogrid[:height, :width]

    # Squared distances to avoid sqrt
    dist_sq = (x_indices - cx) ** 2 + (y_indices - cy) ** 2
    radius_sq = radius ** 2

    # Mask: True for pixels INSIDE or ON the circle
    mask_inside = dist_sq <= radius_sq
    return mask_inside


def get_white_value(dtype):
    """
    Determine the appropriate "white" value based on dtype.
    """
    np_dtype = np.dtype(dtype)

    if np.issubdtype(np_dtype, np.integer):
        return np.iinfo(np_dtype).max
    elif np.issubdtype(np_dtype, np.floating):
        # Common convention for float rasters: 1.0 is white
        return 1.0
    else:
        # Fallback: try 255
        return 255


def process_geotiff(input_path: Path):
    input_path = input_path.resolve()

    with rasterio.open(input_path) as src:
        if src.count != 1:
            raise ValueError(
                f"Expected a single-band grayscale GeoTIFF, but found {src.count} bands."
            )

        profile = src.profile.copy()
        height = src.height
        width = src.width

        # Read the only band
        band = src.read(1)

        # Compute circle mask (True = keep, False = set to white)
        mask_inside = compute_circle_mask(height, width)

        # Determine white value based on dtype
        white_value = get_white_value(band.dtype)

        # Create output array
        out_band = band.copy()
        out_band[~mask_inside] = white_value

    # Build output filename: <stem>-circlecrop<suffix>
    output_path = input_path.with_name(
        f"{input_path.stem}-circlecrop{input_path.suffix}"
    )

    # Write GeoTIFF with same metadata
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(out_band, 1)

    print(f"Output written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Circle-crop a single-band grayscale GeoTIFF.\n"
            "Keeps a center circle that touches the closest border, "
            "sets everything outside to white."
        )
    )
    parser.add_argument(
        "input_geotiff",
        help="Relative path to the input GeoTIFF file (single-band grayscale).",
    )

    args = parser.parse_args()
    input_path = Path(args.input_geotiff)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    process_geotiff(input_path)


if __name__ == "__main__":
    main()
