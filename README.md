# ECDOsim

See the sim here: https://sovrynn.github.io/#/ECDOsim

This repo is solely devoted for the sim pipeline for anyone who wants to extend on this sim.

If you just want the .blend files, look to releases.

.tif files are in `0-files`.

## Sim Pipeline

### Step 1: TIF data generation

First of all, various data is prepared in geocoded format, and saved to GeoTIF format using QGIS into two files - the digital elevation model file used to construct the terrain, and a colored basemap overlaid onto the terrain as a background.

### Step 2: TIF data processing for Blender

The two GeoTIF files are prepared for Blender ingestion using a series of scripts.

### Step 3: Running the sim in Blender

In Blender, the sim is constructed using the assistance of BlenderGIS (Blender add-on) and Blender's built in fluid solver, Mantaflow. The liquid object is constructed by using a Boolean Difference modifier in Blender against the terrain. The liquid is rotated in vortex fashion using a Vortex force field. Several radial attractive forces are carefully applied to mitigate the centrifugal distortion created by rotating fluid.

There are many, many "gotchas" along the way. I'll try to mention as many as I can during the writeup.

# ECDOsim Intro

ECDOsim was developed by myself (Junho) to simulate the effects of an ECDO earth flip. ECDOsim simulates the oceanic displacement (flooding) that would occur during an exothermic core-mantle decoupling Dzhanibekov oscillation (ECDO) cataclysm event, in which the Earth's crust is hypothesized to accelerate and find a new stable rotational position around a rotational axis which intersects two pivot points on Earth's surface. This would lead to a global flood.

ECDOsim bases the projection around a 2D Lambert azimuthal equal-area projection centered around the two pivot points, which lie directly opposite each other on Earth's surface. This projection preserves the radial lines of force imparted onto the fluid by the rotating land, and thus spins the water in a vortex field. The acceleration is fastest at the start and then oscillates to 0 in a pendulum-like motion. The model has been carefully tuned to match the evidence, which includes ancient flood stories, marine fossils, sediment deposits, and salt.

Theoretically, the simulation is supposed to return the exact same results in both projections. However, the simulation is imperfect.

# Other sim notes

## Basic sim notes

- The terrain is scaled up significantly (10x+) in height relative to length and width, which distorts the liquid volume per particle to have less height and more width and length. Since the water depth and volume are also increased when doing this, it shouldn't change the simulation output.
- The terrain is overlaid with a basemap that combines an elevation color gradient with a map showing sedimentary (blue) and volcanic (red) rock surface layers. In later versions, blue dots, representing mostly salt and marine fossils, but also coal/oil/gas mines, were added to the terrain map. In v11, country borders (white lines), tectonic boundaries (black lines), and volcanoes (black dots) were added.
- The cross at the center of the video represents the displacement in position of the Earth (and water) over the duration of the video, oscillating to a displacement of 104 degrees from the initial state, synchronized with the vortex motion of the water.
- Versions v10 and onward also have informational labels in the 4 video corners providing various kinds of information.

## Technical specifications

- There have been eleven versions of the model so far - v1 through v11. Each was released as an improvement upon the previous.
- The fluid resolution was first adjusted in v1, remained the same until v8, and began to increase in each version from v9 onwards. The fluid resolution is proportional to the number of particles.
- The terrain remained the same resolution of about 1.5 million pixels through v9, was increased to 3.4 million pixels in v10, and finally, 13.7 million pixels in v11.
- The simulation's domain spans the Earth's entire surface area of 510 million square kilometers at a depth of ~-10k m low to ~12k m high. The border of the terrain is set to 15k m high.
- The particle count is about 12 million throughout v1-v8, implying a cubic volume of 108 cubic kilometers per liquid particle. This was increased in v9, and again in v10, reaching ~19 million particles in v10 (~68 km^3 per particle).
- The model was developed entirely on my consumer workstation through model v8, using Blender. Half of v9 and the bonus scenarios of v10/v11 were also processed on my computer. However, in v9, I also began to split the workload onto a second high-compute machine graciously lended to me.
- The terrain is modeled as a static mesh, with small frictional and damping forces it exerts on the fluid.

## Regarding model design and tuning

- The design of the model was based on ECDO.
- A total of 9 different vortex pivots, all located near the ECDO pivots, were tested in order to find the inundation results that agreed most with the existing inundation evidence. As part of the tuning, I gave myself the freedom to freely change the pivots in order to better satisfy inundation requirements across the geometric terrain of Earth.
- A variety of Blender "physics forces" were introduced and tested in order to bring the inundation between the two projections as close as possible to each other. The forces exerted on the water have changed throughout all versions of the sim, and while the results between the two pivot projections are still not the same, I believe the results are close enough to still be useful.