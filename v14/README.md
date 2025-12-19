so here's what's going to happen.

i need to scale up the terrain quality which as I understand requires me to increase the res of the input terrain files as well as the sphere's divisions on the terrain.

i'll reconstruct everything on my mac i suppose.

# final changes

timescale 1 -> 0.25 (HUGE DECREASE)

forces extended double time -> might even match the timescale decrease...

fluid increase

I should reduce the forces by 2

# modifications

terrain same

fluid as max as possible -> modular

timescale 0.5 or even 0.25

adjust timescale at least 50% greater

forces remain the same

Approximately 0.25 * 1.5 * 2

I'll run it and adjust on the fly.

here's what I did originally on v8 -> v11:
timescale 1 to 0.5
forces halved
timescale + 50%
fluid res basically double

So what does that do? 0.5 * 0.5 * 1.5 * 2

# terrain limit

using the old base files

it appears teh limit is about 256 and 128 on the uv sphere, and then i load it in

still need to test 4 and 4

it appears to be 3 and 3 the basic limit - 4 and 4 is crashing even on 256 and 128

actually it might have to do with the base file limit

# script 4 - adding rotation

I want you to write a python blender script. IT has one parameter - DEG_PER_FRAME which indicates a number of degrees per frame. It also has a parameter EXTRA_FRAMES which denotes the number of extra keyframes to create after the last "terrain" keyframe.

The script should locate one object named "terrain" in the scene. it has keyframes changing its rotational x y and z position every frame up till a certain frame number.

The script's job is to leave the first frame untouched. but for every other keyframe until the last keyframe of "terrain", and then extending another EXTRA_FRAMES, the script should rotate first DEG_PER_FRAME aroudn the World's z axis, then for the next keyframe rotate 2 * DEG_PER_FRAME, etc ON TOP OF THE EXISTING KEYFRAMED ROTATIONAL X Y Z VALUE of "terrain" for the frame.

Print out the original value, the amount to rotate around the world's static z-axis, and the new overwritten rotational x y and z values. For each frame as you go along.

Do the same thing to object "cross".

Positive values should be clockwise, negative values counterclockwise.

# scirpt sceond try

I need you to write me a somewhat complicated blender script.

First of all, there is an object labeled terrain. Your job is to, for every frame beginning from the first to the last frame with a "Vortex" keyframe, keyframe the x y and z rotational values of the "terrain" and a new "Vortex-dynamic" object. The objects with "vortex" in the name are Vortex force fields.

However, you must do this using a calculation that incorporates the interpolated rotational values of "Vortex" and a SCALE value.

Here's what you'll do:
- Copy the "Vortex" object into a "Vortex-dynamic" object, that has the exact same keyframes and everything is the same except the name.
- For the first frame, keyframe the existing positional values of "terrain". Don't delete any keyframes.

Then, from the second frame to the last frame that has keyframed values in "Vortex", you're going to perform a process that requires some math at every step. You will set two keyframe values at each frame - the rotational x y and z values for "terrain" and "Vortex-dynamic".

Starting from the second frame, for each frame up to and including the last frame with a keyframe for "Vortex" object:

Step 1. 

At the previosu frame, take values:
- Vortex-dynamic interpolated strength value (positive value is counterclockwise, negative value is clockwise)
- Vortex-dynamic interpolated rotational position
- "terrain" rotational x y and z values

Then using those valuse, rotate those "terrain" values by SCALE * strength degrees around the Vortex-dynamic rotational position. That new terrain rotational value should be set to the terrain in the current keyframe.

Step 2.

Take the new terrain rotational x y and z values of step 1 and subtract from them the "terrain" object rotational x y z values in frame 1. If that is S, then calculate the interpolated "Vortex" object rotational value at the current frame. Add S to that. Set that new rotational x y and z value to "Vortex-dynamic" as a current keyframe.

Throughout this process, assume all objects (Vortex, Vortex-dynamic, and terrain) are centered at the origin, because they are.

As you process each frame, print out all incorporated values (total rotational displacement from the first frame, degrees rotated, etc) to console.

Once finished print out a completion message to console as well.

# script

I need you to write me a somewhat complicated blender script.

First of all, there is an object labeled terrain. Your job is to, for every frame beginning from the first to the last frame with a Vortex keyframe, keyframe the x y and z rotational vvalues of the "terrain" object.

However, you must do this using a calculation that incorporates the interpolated strength values of a Vortex force field named "Vortex", a SCALE value, and a temporary Vortex force field that you rotate along with the "terrain" object on every keyframe.

Here's what you'll do:
- Copy the "Vortex" object into a "Vortex-dynamic" object, that has the exact same keyframes and everything is the same except the name.
- For the first frame, keyframe the existing positional values of "terrain" and "Vortex-dynamic". Delete all other keyframes.
- Then, from the second frame to the last frame that has keyframed values in "Vortex", you're going to perform a process that requires some math at every step. You're going to take the rotational orientation of the Vortex at the previous frame, take the Vortex interpolated strength value (positive value is clockwise, negative value is counterclockwise) and rotate the terrain and Vortex-dynamic objects for SCALE * strength degrees at that keyframe. However, for the Vortex-dynamic, you have to also add in the interpolated rottaional x y z values for the original Vortex force.

You'll have to take the rotation orientation of the Vortex into account to perform the SCALE * strength degree rotation properly (there are 3 rotation values for x y and z). Therefore, from the first frame to the last frame with a keyframe in Vortex, you're going to add that many keyframes with a new rotational x y z value at each keyframe. Don't modify any other properties in the keyframes.

Throughout this process, assume all objects (Vortex, Vortex-dynamic, and terrain) are centered at the origin, because they are.

As you process each frame, print out all incorporated values (total rotational displacement from the first frame, degrees rotated, etc) to console.

Once finished print out a completion messaget o console as well.

## MODIFY

Then, from the second frame to the last frame that has keyframed values in "Vortex", you're going to perform a process that requires some math at every step.

You're going to dynamically update the rotational position x y z values of Vortex-dynamic and use that to also calculate a rotational position of "terrain".

Starting from the second frame, you're going to take the rotational orientation of Vortex-dynamic at the previous frame. Take its interpolated strength value (positive value is counterclockwise, negative value is clockwise) and rotate the terrain SCALE * strength degrees around the Vortex-dynamic z-axis and keyframe that rotational x y and z value.

You'll also need to set a new keyframe for the new rotational position of Vortex-dynamic. You'll have to find the net displacement of the "terrain" at that keyframe from the original rotational position of "terrain" at frame 1. Then, add that "terrain" rotational displacement to the original rotational position of "Vortex-dynamic" at frame 1 to get the new rotational position of "Vortxe-dynamic" at the current frame.

# recreating the opposite of the vortex

So what you have to do 

positive vortex strength is clockwise

negative vortex strength is counterclockwise

You need to factor in the strength and rotational axis of the vortex

And then multiply that by an adjustable SCALE value

And then keyframe the rotation of the ball every moment

# rotation marker

The only annoying thing here is adding an informational rotation gui marker.

i think i'll start a pole at x thickness. color it based on the polarity of the rotation. increase its thickness based on the speed of the rotation, and rotate it along with the vortex force.

# scirpt

Write a python blender script that does the following. THere is a vortex force field named "Vortex" and a cylinder named "cross". The script should remove all keyframes for "cross". Then, for every keyframe of Vortex, the script should add a keyframe to cross based on the following:

When the vortex force strength value is positive, the script should color it color X (parameterized in the script). When the strength value is 0. the color should be white. when the strength value is negative, the color should be Y. Default, make it blue and red.

Then, the cylinder has a base x and y scale of X. Whenever the vortex force is 0, it should have that scale X. But if the vortex force is 1, the scale should be 2x, and if the vortex force is 2, the scale should be 3x, etc. Keyframe the width of the cylinder by a scale of (1 + vortex strength). Finally, for each keyframe, set the rotational x y and z position values of "cross" to be the same as "Vortex".

Write each modified keyframe and values to console.