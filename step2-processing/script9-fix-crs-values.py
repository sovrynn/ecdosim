#!/usr/bin/env python3
import sys
import os
import rasterio
from rasterio.transform import from_origin

FIFTEEN_ARCSEC = 15.0 / 3600.0  # 0.004166666666666667 degrees

def main():
    if len(sys.argv) != 2:
        print("Usage: python retag_to_geographic_15arcsec.py <relative_path_to_tif>")
        sys.exit(1)

    in_path = sys.argv[1]
    if not os.path.exists(in_path):
        print(f"Error: file not found: {in_path}")
        sys.exit(1)

    with rasterio.open(in_path) as src:
        profile = src.profile.copy()

        # Build a new transform:
        # - origin at (0, 0) (west=0, north=0)
        # - pixel size: 15 arcsec in both x and y (y is negative for north-up)
        transform = from_origin(
            0.0,  # west (lon)
            0.0,  # north (lat)
            FIFTEEN_ARCSEC,  # x pixel size (deg)
            FIFTEEN_ARCSEC   # y pixel size (deg) -> from_origin makes it negative internally
        )

        # Update profile: set CRS to EPSG:4326, keep size/bands/dtype/etc.
        profile.update(
            crs="EPSG:4326",
            transform=transform
        )

        # Prepare output path (same directory, slightly modified name)
        in_dir = os.path.dirname(os.path.abspath(in_path))
        base, ext = os.path.splitext(os.path.basename(in_path))
        out_name = f"{base}_wgs84_15arcsec_from0_0{ext}"
        out_path = os.path.join(in_dir, out_name)

        # Copy all bands as-is; only georeferencing changes
        data = src.read()
        with rasterio.open(out_path, "w", **profile) as dst:
            dst.write(data)
            # Copy dataset-level tags if any
            try:
                dst.update_tags(**src.tags())
            except Exception:
                pass
            # Copy per-band tags if any
            for i in range(1, src.count + 1):
                try:
                    dst.update_tags(i, **src.tags(i))
                except Exception:
                    pass

    print("✅ Re-tagged GeoTIFF written:")
    print(f"   {out_path}")
    print("   CRS: EPSG:4326 (WGS 84)")
    print(f"   Pixel size: {FIFTEEN_ARCSEC} deg (≈ 15 arcsec)")
    print("   Origin (upper-left): (0°, 0°)")
    print("   Note: pixel values are unchanged; only georeferencing was modified.")

if __name__ == "__main__":
    main()
