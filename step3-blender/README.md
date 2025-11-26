# Step 3: Blender

Finally, the two tif files are loaded into blender using BlenderGIS.

"DEM raw data build" option is used first, on the dem file, which generates a blank terrain object. Adjusting the "step" is used to adjust the terrain resolution - early sim versions used 3, v10 used 2, and v11 uses 1 (max).

Then, "basemap on mesh" option is used to overlay the basemap onto the terrain.

Afterwards, blender is used for everything - from the sim, to the renders. The fluid sim uses the classic mantaflow solver rather than the newer geometry nodes.