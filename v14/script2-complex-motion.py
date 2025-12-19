import bpy
import math
from mathutils import Quaternion, Vector, Euler

# -----------------------
# USER SETTINGS
# -----------------------
SCALE = 8.0  # degrees multiplier: degrees_rotated_per_frame = SCALE * strength

TERRAIN_NAME = "terrain"
VORTEX_NAME = "Vortex"
VORTEX_DYN_NAME = "Vortex-dynamic"

# Choose an Euler order to use when writing rotations
EULER_ORDER = 'XYZ'

# -----------------------
# HELPERS
# -----------------------
def get_obj(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if not obj:
        raise RuntimeError(f"Object '{name}' not found.")
    return obj

def get_action_frame_range_from_object(obj: bpy.types.Object):
    ad = obj.animation_data
    if not ad or not ad.action:
        raise RuntimeError(f"Object '{obj.name}' has no animation action/keyframes.")
    action = ad.action

    frames = []
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            frames.append(kp.co.x)

    if not frames:
        raise RuntimeError(f"Object '{obj.name}' action has no keyframe points.")

    # Keyframes can be floats; treat frame indices as ints for stepping
    fmin = int(round(min(frames)))
    fmax = int(round(max(frames)))
    return fmin, fmax

def ensure_vortex_dynamic(vortex_obj: bpy.types.Object) -> bpy.types.Object:
    # If exists already, reuse it (do not create duplicates)
    existing = bpy.data.objects.get(VORTEX_DYN_NAME)
    if existing:
        return existing

    new_obj = vortex_obj.copy()
    # Copy object "data" if present (empties often have none)
    if vortex_obj.data:
        new_obj.data = vortex_obj.data.copy()

    new_obj.name = VORTEX_DYN_NAME

    # Copy animation data/action so it has the same keyframes initially
    if vortex_obj.animation_data and vortex_obj.animation_data.action:
        new_obj.animation_data_create()
        new_obj.animation_data.action = vortex_obj.animation_data.action.copy()

    # Link into same collections as original (fallback: scene collection)
    if vortex_obj.users_collection:
        for col in vortex_obj.users_collection:
            col.objects.link(new_obj)
    else:
        bpy.context.scene.collection.objects.link(new_obj)

    return new_obj

def evaluated_state(obj: bpy.types.Object, depsgraph):
    obj_eval = obj.evaluated_get(depsgraph)

    # Rotation as quaternion for robust composition
    q = obj_eval.matrix_world.to_quaternion()

    # Force-field strength (for Vortex objects)
    strength = None
    if hasattr(obj_eval, "field") and obj_eval.field:
        strength = float(obj_eval.field.strength)

    return q, strength, obj_eval

def quat_to_euler_xyz(q: Quaternion) -> Euler:
    e = q.to_euler(EULER_ORDER)
    return Euler((e.x, e.y, e.z), EULER_ORDER)

def euler_deg(e: Euler):
    return (math.degrees(e.x), math.degrees(e.y), math.degrees(e.z))

def wrap_angle_deg(a):
    # keep readable in prints
    while a > 180.0:
        a -= 360.0
    while a < -180.0:
        a += 360.0
    return a

def euler_delta_deg(e_from: Euler, e_to: Euler):
    # human-friendly delta (not used for math)
    df = euler_deg(e_from)
    dt = euler_deg(e_to)
    d = (wrap_angle_deg(dt[0]-df[0]), wrap_angle_deg(dt[1]-df[1]), wrap_angle_deg(dt[2]-df[2]))
    return d

# -----------------------
# MAIN
# -----------------------
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()

terrain = get_obj(TERRAIN_NAME)
vortex = get_obj(VORTEX_NAME)
vortex_dyn = ensure_vortex_dynamic(vortex)

# Determine processing range from Vortex keyframes
frame_first, frame_last = get_action_frame_range_from_object(vortex)

print("------------------------------------------------------------")
print(f"[INFO] Vortex keyframe range: {frame_first} -> {frame_last}")
print(f"[INFO] Using SCALE = {SCALE}")
print(f"[INFO] Objects: terrain='{terrain.name}', vortex='{vortex.name}', vortex_dyn='{vortex_dyn.name}'")
print("------------------------------------------------------------")

# Frame 1 (first keyframed frame): keyframe terrain location (do NOT delete anything)
scene.frame_set(frame_first)
terrain.keyframe_insert(data_path="location", frame=frame_first)
print(f"[INFO] Keyframed terrain.location at frame {frame_first} (existing keyframes preserved).")

# Store "terrain rotation at frame 1" as reference for displacement
# Use evaluated quaternion for consistency with interpolation
scene.frame_set(frame_first)
terrain_q_first, _, _ = evaluated_state(terrain, depsgraph)

# Process frames from second frame up to last
for f in range(frame_first + 1, frame_last + 1):
    prev_f = f - 1

    # --- Gather PREVIOUS frame evaluated state (Step 1 inputs) ---
    scene.frame_set(prev_f)

    terrain_q_prev, _, _ = evaluated_state(terrain, depsgraph)
    vortex_dyn_q_prev, strength_prev, _ = evaluated_state(vortex_dyn, depsgraph)

    if strength_prev is None:
        raise RuntimeError(f"'{vortex_dyn.name}' does not appear to have a force field strength (not a Vortex force field?).")

    degrees_to_rotate = -SCALE * strength_prev
    radians_to_rotate = math.radians(degrees_to_rotate)

    # Axis = Vortex-dynamic local Z axis, rotated into world space by its rotation
    axis_world = (vortex_dyn_q_prev @ Vector((0.0, 0.0, 1.0))).normalized()
    rot_q = Quaternion(axis_world, radians_to_rotate)

    # Apply world-space rotation to terrain rotation
    terrain_q_new = rot_q @ terrain_q_prev

    # --- Write terrain rotation at CURRENT frame (Step 1 result) ---
    scene.frame_set(f)
    terrain.rotation_mode = EULER_ORDER
    terrain.rotation_euler = quat_to_euler_xyz(terrain_q_new)
    terrain.keyframe_insert(data_path="rotation_euler", frame=f)

    # --- Step 2: displacement from terrain frame_first, applied to current Vortex rotation ---
    displacement_q = terrain_q_new @ terrain_q_first.inverted()

    # Get CURRENT frame interpolated Vortex rotation
    vortex_q_cur, _, _ = evaluated_state(vortex, depsgraph)

    vortex_dyn_q_new = displacement_q @ vortex_q_cur

    # Write Vortex-dynamic rotation at CURRENT frame
    vortex_dyn.rotation_mode = EULER_ORDER
    vortex_dyn.rotation_euler = quat_to_euler_xyz(vortex_dyn_q_new)
    vortex_dyn.keyframe_insert(data_path="rotation_euler", frame=f)

    # --- Prints ---
    terrain_e_prev = quat_to_euler_xyz(terrain_q_prev)
    terrain_e_new  = quat_to_euler_xyz(terrain_q_new)
    terrain_e_first = quat_to_euler_xyz(terrain_q_first)
    disp_e = quat_to_euler_xyz(displacement_q)
    vortex_e_cur = quat_to_euler_xyz(vortex_q_cur)
    vortexdyn_e_new = quat_to_euler_xyz(vortex_dyn_q_new)

    print("------------------------------------------------------------")
    print(f"[FRAME {f}] prev_frame={prev_f}")
    print(f"  Step 1 inputs:")
    print(f"    Vortex-dynamic strength(prev) = {strength_prev:.6f}")
    print(f"    Degrees rotated = SCALE * strength = {SCALE} * {strength_prev:.6f} = {degrees_to_rotate:.6f} deg")
    print(f"    Axis(world) = ({axis_world.x:.6f}, {axis_world.y:.6f}, {axis_world.z:.6f})")
    print(f"    terrain rot(prev) deg = {tuple(round(x, 6) for x in euler_deg(terrain_e_prev))}")
    print(f"  Step 1 result:")
    print(f"    terrain rot(new)  deg = {tuple(round(x, 6) for x in euler_deg(terrain_e_new))}")
    print(f"  Step 2:")
    print(f"    terrain rot(frame1) deg = {tuple(round(x, 6) for x in euler_deg(terrain_e_first))}")
    print(f"    total displacement (quat->euler) deg = {tuple(round(x, 6) for x in euler_deg(disp_e))}")
    print(f"    Vortex rot(cur, interpolated) deg = {tuple(round(x, 6) for x in euler_deg(vortex_e_cur))}")
    print(f"    Vortex-dynamic rot(new) deg = {tuple(round(x, 6) for x in euler_deg(vortexdyn_e_new))}")
    print("------------------------------------------------------------")

# Restore original current frame if you want; optional
# scene.frame_set(frame_first)

print(f"[DONE] Completed keyframing terrain + Vortex-dynamic rotations from frame {frame_first} to {frame_last}.")
