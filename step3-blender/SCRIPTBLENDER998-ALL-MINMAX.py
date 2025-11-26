import bpy

def analyze_fluid_particle_counts():
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    domain_obj = bpy.data.objects.get("Domain")  # Change name if needed
    if domain_obj is None:
        print("Error: Domain object named 'Domain' not found.")
        return

    evaluated_domain = domain_obj.evaluated_get(depsgraph)

    if not evaluated_domain.particle_systems:
        print("Error: No particle systems found on the domain object. Make sure fluid particles (Tracer/Generated) are enabled and baked.")
        return

    particle_system = evaluated_domain.particle_systems[0]

    min_particles = None
    max_particles = None
    min_frame = None
    max_frame = None

    print("\nAnalyzing frames...\n")

    for frame in range(scene.frame_start, scene.frame_end + 1):
        scene.frame_set(frame)   # Move to frame
        depsgraph.update()       # Update dependency graph

        particles = particle_system.particles

        if not particles:
            print(f"Frame {frame}: No particles (possibly not baked). Skipping...")
            continue

        count = len(particles)
        print(f"Frame {frame}: {count} particles")

        if min_particles is None or count < min_particles:
            min_particles = count
            min_frame = frame

        if max_particles is None or count > max_particles:
            max_particles = count
            max_frame = frame

    print("\n--- Summary ---")
    if min_particles is not None:
        print(f"Minimum particles: {min_particles} on frame {min_frame}")
        print(f"Maximum particles: {max_particles} on frame {max_frame}")
    else:
        print("No baked frames with particles were found.")

# Run the function
analyze_fluid_particle_counts()
