Well well.

# prompt

write a python blender script that finds one vortex force named "Vortex". The script has one parameter which contains a single string with space-separated numbers in groups of 3. in a single group of 3, the first number is the frame nmuber, the second number is the vortex strength value, and the third number is the vortex flow value. Based on the value of the parameter, the scirpt should first delete all existing keyframes int he Vortex force in the current Blender scene, and then it should apply the keyframe strength and flow values to the Vortex force. Print out each keyframe as you add it - the frame number, strength and flow values.

# prompt

write a python blender script that finds one vortex force named "Vortex". The script should reach each keyframe of that Vortex and print out one line to console containing each keyframe's frame number, strength parameter value, adn flow paramater value in the format "X Y Z ", combining the numbers so that its one space separated sequnece of numbers where each group of 3 corresponds to one keyframe, in order that they're in. print the single line of space-separated numbers to console.

# prompt

Write a python blender script that takes one input file path (relative) as an input arg, a relative geotif file.

The sciprt should read it in and clip it so its bounds are the mercator boundaries (lon -180 to 180, lat -90 to 90).

The metadata should of course also be named.

Naturally the raster should be clipped.

The output file pixel dimensions should be exactly 2 long and 1 tall.

make sure the script works with both grayscale and rgb input value bands.

THe sciprt should then write the modified tif file to the same path as the input file and same filename but with -clipped appended to the filename.

