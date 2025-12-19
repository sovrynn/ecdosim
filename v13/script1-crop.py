import os
import sys

# Optional in Blender, only needed if you want to resolve relative paths
try:
    import bpy
    HAVE_BPY = True
except ImportError:
    HAVE_BPY = False

import rasterio
from rasterio.windows import from_bounds
import numpy as np


def get_script_arg():
    """
    Get a single input path argument.

    Supports:
      - Plain Python:
          python script1-crop.py basemap.tif
      - Blender:
          blender -b -P script1-crop.py -- basemap.tif
    """
    argv = sys.argv

    if "--" in argv:
        # Blender-style: everything after -- is for the script
        script_args = argv[argv.index("--") + 1 :]
    else:
        # Normal Python: args after script name
        script_args = argv[1:]

    if len(script_args) < 1:
        raise SystemExit(
            "Error: Expected one argument: relative path to input GeoTIFF\n\n"
            "Examples:\n"
            "  Python : python script1-crop.py path/to/input.tif\n"
            "  Blender: blender -b -P script1-crop.py -- path/to/input.tif"
        )

    if len(script_args) > 1:
        print("Warning: More than one argument provided; using the first one.")

    return script_args[0]


def resolve_path(rel_path: str) -> str:
    """
    Resolve a relative path. If running inside Blender and a .blend file
    is loaded, use its directory as the base. Otherwise use CWD.
    """
    if HAVE_BPY and bpy.data.filepath:
        base_dir = os.path.dirname(bpy.data.filepath)
        return os.path.abspath(os.path.join(base_dir, rel_path))
    else:
        return os.path.abspath(rel_path)


def build_output_path(input_path: str) -> str:
    """
    Append '-clipped' before the file extension.
    e.g. 'foo.tif' -> 'foo-clipped.tif'
    """
    directory, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    clipped_name = f"{name}-clipped{ext}"
    return os.path.join(directory, clipped_name)


def clip_to_world_bounds(input_tif: str, output_tif: str):
    # World bounds in lon/lat degrees
    world_left, world_bottom, world_right, world_top = -180.0, -90.0, 180.0, 90.0

    with rasterio.open(input_tif) as src:
        if src.crs is None:
            raise RuntimeError(
                "Input GeoTIFF has no CRS defined. "
                "This script expects a geographic CRS (e.g. EPSG:4326)."
            )

        # Optional sanity check – comment this out if you know what you’re doing
        if not src.crs.is_geographic:
            raise RuntimeError(
                f"Input CRS {src.crs} is not geographic (lat/lon). "
                "The script currently expects degrees with lon/lat. "
                "Reproject your raster to EPSG:4326 first."
            )

        # Current dataset bounds
        src_bounds = src.bounds

        # Intersection of dataset bounds with world lon/lat bounds
        left = max(src_bounds.left, world_left)
        bottom = max(src_bounds.bottom, world_bottom)
        right = min(src_bounds.right, world_right)
        top = min(src_bounds.top, world_top)

        if left >= right or bottom >= top:
            raise RuntimeError(
                "The raster does not overlap the world bounds "
                "[-180, 180] x [-90, 90]. Nothing to clip."
            )

        # Compute window in pixel coordinates for that bounding box
        window = from_bounds(left, bottom, right, top, transform=src.transform)

        # Read data within the window (all bands)
        data = src.read(window=window)

        # Derive new transform and dimensions
        transform = rasterio.windows.transform(window, src.transform)
        _, height, width = data.shape

        # Copy metadata & update with new transform/size
        dst_meta = src.meta.copy()
        dst_meta.update(
            {
                "transform": transform,
                "width": width,
                "height": height,
                # preserve band count, dtype, crs, nodata, etc.)
            }
        )

        # Write out clipped GeoTIFF
        with rasterio.open(output_tif, "w", **dst_meta) as dst:
            dst.write(data)


def main():
    rel_input_path = get_script_arg()
    input_path = resolve_path(rel_input_path)

    if not os.path.exists(input_path):
        raise SystemExit(f"Input file does not exist: {input_path}")

    output_path = build_output_path(input_path)

    print(f"Input : {input_path}")
    print(f"Output: {output_path}")
    print("Clipping raster to bounds [-180, 180] x [-90, 90] (lon/lat) ...")

    clip_to_world_bounds(input_path, output_path)

    print("Done.")


if __name__ == "__main__":
    main()
