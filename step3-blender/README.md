# Step 3: Blender

Finally, the two tif files are loaded into blender using BlenderGIS.

"DEM raw data build" option is used first, on the dem file, which generates a blank terrain object. Adjusting the "step" is used to adjust the terrain resolution - early sim versions used 3, v10 used 2, and v11 uses 1 (max).

Then, "basemap on mesh" option is used to overlay the basemap onto the terrain.

Afterwards, blender is used for everything - from the sim, to the renders. The fluid sim uses the classic mantaflow solver rather than the newer geometry nodes.

## blender forces

a point vortex force with the flow parameter is used to swing the water in a circle with the desired strength.

Multiple pairs of partially overlapping and opposite point forces are used to pull the water inwards, as you will see if you inspect the .blend files.

## techniques to achieve better performance or lower compute requirements

1. reduce fluid resolution - domain subdivisions in blender
2. reduce terrain resolution - delete the old terrain and load a new terrain+basemap with more pixels per point
3. use a moduler bake to squeeze about 50% more resolution out of the same hardware

past that, you just need to upgrade your hardware.

## scripts

I use various scripts within Blender (recommend starting it from the command line using ex. caffeinate) to handle the keyframes for modifying vortex forces etc

by the end, I essentially exclusively used:
- script4 multiply 1.5 : multiplying forces (but not vortex)
- script91 print all keyframes and values for forces and vortex
- script92 scale vortex: adjust vortex strength
- script97: adjust timescale by simply scaling duration between keyframes
- script996/997: for adding the cross rotation which is derived from the vortex