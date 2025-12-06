#!/usr/bin/env python3

import argparse
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine

# Thickness of the white border, in pixels
BORDER_THICKNESS_PIXELS = 100  # <-- change this as needed


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


def add_border(input_path: Path):
    input_path = input_path.resolve()

    with rasterio.open(input_path) as src:
        profile = src.profile.copy()
        height = src.height
        width = src.width
        count = src.count

        if count not in (1, 4):
            raise ValueError(
                f"Expected either a single-band grayscale or 4-band RGB(A) GeoTIFF, "
                f"but found {count} bands."
            )

        # Read all bands: shape (count, height, width)
        data = src.read()

        print(f"Original dimensions: {width} x {height}")

        border = BORDER_THICKNESS_PIXELS

        # New dimensions
        new_height = height + 2 * border
        new_width = width + 2 * border

        # Determine white value based on dtype
        white_value = get_white_value(data.dtype)

        # Create output array filled with white
        out_data = np.full(
            (count, new_height, new_width),
            fill_value=white_value,
            dtype=data.dtype,
        )

        # Paste original image into the center
        out_data[:, border:border + height, border:border + width] = data

        # Update transform so original pixels keep their georeferenced location
        # New transform T' such that T' * (border, border) = T * (0, 0)
        # => T' = T * translation(-border, -border)
        transform = src.transform
        new_transform = transform * Affine.translation(-border, -border)

        # Update profile
        profile.update(
            height=new_height,
            width=new_width,
            transform=new_transform,
        )

    print(f"New dimensions: {new_width} x {new_height}")

    # Build output filename: <stem>-border<suffix>
    output_path = input_path.with_name(
        f"{input_path.stem}-border{input_path.suffix}"
    )

    # Write GeoTIFF with updated metadata
    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(out_data)

    print(f"Output written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Add a white pixel border around a GeoTIFF.\n"
            "- Supports single-band grayscale or 4-band RGB(A).\n"
            "- Border thickness is set in the script via BORDER_THICKNESS_PIXELS."
        )
    )
    parser.add_argument(
        "input_geotiff",
        help="Relative path to the input GeoTIFF file.",
    )

    args = parser.parse_args()
    input_path = Path(args.input_geotiff)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    add_border(input_path)


if __name__ == "__main__":
    main()
