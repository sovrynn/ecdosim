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
        profile = src.profile.copy()
        height = src.height
        width = src.width

        # Read all bands
        data = src.read()  # shape: (count, height, width)

        if src.count not in (1, 4):
            raise ValueError(
                f"Expected either a single-band grayscale or 4-band RGB(A) GeoTIFF, "
                f"but found {src.count} bands."
            )

        # Compute circle mask (True = keep, False = set to white)
        mask_inside = compute_circle_mask(height, width)
        mask_outside = ~mask_inside

        # Determine white value based on dtype of the underlying array
        white_value = get_white_value(data.dtype)

        out_data = data.copy()

        if src.count == 1:
            # Single-band case: set outside-circle pixels to white in that band
            out_data[0, mask_outside] = white_value

        elif src.count == 4:
            # 4-band case: assume first 3 bands are RGB, 4th is alpha.
            # Set RGB bands to white outside the circle, keep alpha as-is.
            out_data[0:3, mask_outside] = white_value

            # If you also want to make outside fully transparent, uncomment:
            # out_data[3, mask_outside] = 0

    # Build output filename: <stem>-circlecrop<suffix>
    output_path = input_path.with_name(
        f"{input_path.stem}-circlecrop{input_path.suffix}"
    )

    # Write GeoTIFF with same metadata
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(out_data)

    print(f"Output written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Circle-crop a GeoTIFF.\n"
            "- For single-band grayscale: keeps a center circle and sets outside to white.\n"
            "- For 4-band RGB(A): keeps a center circle, sets RGB outside to white."
        )
    )
    parser.add_argument(
        "input_geotiff",
        help=(
            "Relative path to the input GeoTIFF file "
            "(single-band grayscale or 4-band RGB(A))."
        ),
    )

    args = parser.parse_args()
    input_path = Path(args.input_geotiff)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    process_geotiff(input_path)


if __name__ == "__main__":
    main()
