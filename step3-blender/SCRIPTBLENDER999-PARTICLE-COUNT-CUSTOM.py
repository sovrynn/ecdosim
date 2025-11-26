import bpy

def analyze_fluid_particle_counts(frame_step=1, start_frame=1, end_frame=5):
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()

    domain_obj = bpy.data.objects.get("DOMAIN")  # Change if needed
    if domain_obj is None:
        print("Error: Domain object named 'Domain' not found.")
        return

    evaluated_domain = domain_obj.evaluated_get(depsgraph)

    if not evaluated_domain.particle_systems:
        print("Error: No particle systems found on the domain object.")
        return

    particle_system = evaluated_domain.particle_systems[0]

    min_particles = None
    max_particles = None
    min_frame = None
    max_frame = None

    # Use provided range or default to scene's range
    start = start_frame if start_frame is not None else scene.frame_start
    end = end_frame if end_frame is not None else scene.frame_end

    print(f"\nAnalyzing every {frame_step} frames from frame {start} to {end}...\n")

    for frame in range(start, end + 1, frame_step):
        scene.frame_set(frame)
        depsgraph.update()

        particles = particle_system.particles

        if not particles:
            print(f"Frame {frame}: No particles (skipping...)")
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
        print(f"Minimum particles: {min_particles} at frame {min_frame}")
        print(f"Maximum particles: {max_particles} at frame {max_frame}")
    else:
        print("No valid frames with particles were found.")

# Run the function with custom frame range
analyze_fluid_particle_counts(frame_step=50, start_frame=1, end_frame=200)
