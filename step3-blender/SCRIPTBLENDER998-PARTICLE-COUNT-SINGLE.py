import bpy

def get_fluid_particle_count():
    # Get the active scene and dependency graph
    scene = bpy.context.scene
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    # Try to find the fluid domain object
    domain_obj = bpy.data.objects.get("DOMAIN") # Replace "Domain" with your actual domain object name if different
    
    if domain_obj is None:
        print("Error: Domain object named 'Domain' not found.")
        return

    # The fluid simulation creates a particle system on the domain object
    evaluated_domain = domain_obj.evaluated_get(depsgraph)
    
    # Check if there are particle systems
    if not evaluated_domain.particle_systems:
        print("Error: No particle systems found on the domain object. Ensure fluid particles (e.g., Tracer, Generate) are enabled and baked.")
        return

    # Access the first particle system (usually the fluid particles)
    particle_system = evaluated_domain.particle_systems[0]
    particles = particle_system.particles
    
    # Get the total count of particles for the current frame
    total_particles = len(particles)

    print(f"Frame {scene.frame_current}: Total fluid particles = {total_particles}")

# Run the function
get_fluid_particle_count()
