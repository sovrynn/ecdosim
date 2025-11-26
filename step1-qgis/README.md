# Step 1: Data Prep

QGIS is used to generate two files:
1. elevation tif file, rgb but grayscale in reality
2. basemap tif file, rgb

These files must be generated together without moving the QGIS viewport, because the two files need to line up exactly - the same location should be in the same pixel position in both files.

## setup qgis environment with desired projection

A custom CRS environment is setup by using a "basefile" that is coded to have the desired custom CRS. In this case, its a Lambert Azimuthal Equal Area projection. A custom proj4 CRS code is used for this ie:

+proj=laea +lat_0=20 +lon_0=-50 +ellps=WGS84 +units=m

## load data files

Then, the desired data is loaded in.

GEBCO is used for the DEM. The gradient goes from -10513 to 15000 - the max elevation is ~8000, but the terrain "out-of-bounds" border is set to 15000 m.

The basemap is a combination of a lot of data - geology, KMLs, and a color-graded GEBCO overlay. Opacity and marker styles are adjusted for optimal visibility. Two GEBCO DEMs, one for the sea and one for the land, are used to create two separate color gradients.

## Export data files

the data files are exported to have the exact same pixel resolution and the exact same "alignment".

QGIS creates white pixels between the GEBCO dem layers very often, and to minimize this, the zoom must be constantly adjusted to try and find a view with minimum pixelation. These pixel defects affect the terrain, so they should be minimized in the key area (center) of the dem.

Once you adjust the viewport until you find a minimally pixelated dem, export the dem and basemap to tif files. And the second step of the sim is ready to begin processing.