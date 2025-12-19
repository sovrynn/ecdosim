Generally using all the old shiz - simply scaling up v14.

On v15 bonus scenario though, I need a new script for denoting the cross. I'll just leave it at the exact pivot and have it change color and size.

# script

Write a python blender script that does the following. it should locate an object named "cross". Delete all keyframes on it. Sets its rotational x y and z values to 0,0,0.

Then, for each keyframe of the Vortex force field, "cross" should have its color and x and y scale keyframed based on the polarity and strength of the vortex force field.

If the force strength value is 0, the script should change the color of the "cross" material to white. If the force is negative, the color should be red, and if positive, the color should be blue. Additionally, based on the value of the vortex strength, the script should scale the x and y scale values by * (1 + 10 * strength) - so if the vortex strength is 0.1, the script should scale the x and y scale values of "cross" to be * (1 + 1) so 2x whatever it was.