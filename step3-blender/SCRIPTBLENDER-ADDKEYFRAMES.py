import bpy

def find_objects_by_field_type(field_type):
    """Return list of objects whose physics field type matches field_type."""
    return [obj for obj in bpy.data.objects
            if getattr(obj, "field", None) and obj.field.type == field_type]

def get_strength_fcurve(obj):
    """Return the FCurve for the object's field strength, if it exists."""
    ad = getattr(obj, "animation_data", None)
    if not ad or not ad.action:
        return None
    for fc in ad.action.fcurves:
        if fc.data_path == "field.strength":
            return fc
    return None

# --- Locate the force field objects ---
vortex_list = find_objects_by_field_type('VORTEX')
if not vortex_list:
    raise RuntimeError("No VORTEX force field found in the scene.")
if len(vortex_list) > 1:
    print("Warning: More than one VORTEX found. Using the first one.")

vortex = vortex_list[0]

plain_forces = find_objects_by_field_type('FORCE')
if len(plain_forces) < 2:
    raise RuntimeError("Fewer than two plain FORCE fields found. Need exactly two.")

# Use the first two FORCE fields found
plain_a, plain_b = plain_forces[:2]

# --- Get the vortex strength keyframes ---
vortex_fc = get_strength_fcurve(vortex)
if not vortex_fc or not vortex_fc.keyframe_points:
    raise RuntimeError(f"Vortex '{vortex.name}' has no keyframes on field.strength.")

# Sort keyframes by frame (x)
keyframes = sorted(vortex_fc.keyframe_points, key=lambda kp: kp.co.x)

print(f"Processing {len(keyframes)} keyframes from vortex '{vortex.name}'...")
print(f"Target plain forces: '{plain_a.name}' and '{plain_b.name}'")

# --- For each vortex keyframe: mirror |strength| to both plain forces and keyframe them ---
for kp in keyframes:
    frame = int(round(kp.co.x))
    # Evaluate the vortex strength at this frame (robust if handles/curves change)
    vortex_strength = vortex_fc.evaluate(frame)
    mirrored = abs(vortex_strength)

    # Set scene to the frame so any dependent evaluations are consistent (not strictly required)
    bpy.context.scene.frame_set(frame)

    # Set and keyframe both plain forces
    for pf in (plain_a, plain_b):
        pf.field.strength = mirrored
        pf.keyframe_insert(data_path="field.strength", frame=frame)

    # Console log
    print(f"Frame {frame}: set plain forces to strength = {mirrored:.6f}")

print("Done.")
