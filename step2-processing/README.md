# Step 2: tif file processing for blender

Next, a series of steps must be done in order to prepare the files for blender ingestion.

First, the DEM tif file's borders are adjusted in GIMP to change them from the lowest elevation to the highest elevation (white -> black IIRC).

Next, the DEM is scaled from rgb to a 0->1 grayscale band, and the tif file is modified to have 4 rgb-opacity bands to have 1 grayscale band.

In later sim versions the DEM is chopped off at the bottom (concatenate -t 0.18) which is used for domain optimization (and only removes a tiny fraction of ocean volume over << 1% of the surface area)

Finally, the files are cropped (must use the exact same crop!) and the CRS, which was lambert azimuthal before, is hardcoded to mercator without changing the actual pixel bands.

A last script tweaks some additional tif metadata to get blender to accept the files.