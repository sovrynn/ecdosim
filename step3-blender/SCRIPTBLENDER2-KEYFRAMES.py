import bpy

def find_vortex():
    vortices = [o for o in bpy.data.objects if getattr(o, "field", None) and o.field.type == 'VORTEX']
    if not vortices:
        raise RuntimeError("No VORTEX force field found.")
    if len(vortices) > 1:
        print("Warning: More than one VORTEX found. Using the first:", [o.name for o in vortices])
    return vortices[0]

def require_force_named(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Required FORCE object named '{name}' not found.")
    if not getattr(obj, "field", None) or obj.field.type != 'FORCE':
        raise RuntimeError(f"Object '{name}' exists but is not a plain FORCE field.")
    return obj

def get_strength_fcurve(obj):
    ad = getattr(obj, "animation_data", None)
    if not ad or not ad.action:
        return None
    for fc in ad.action.fcurves:
        if fc.data_path == "field.strength":
            return fc
    return None

# --- Locate required objects ---
vortex = find_vortex()
attractive = require_force_named("attractive")
repulsive = require_force_named("repulsive")

# --- Get vortex keyframes on field.strength ---
v_fc = get_strength_fcurve(vortex)
if not v_fc or not v_fc.keyframe_points:
    raise RuntimeError(f"Vortex '{vortex.name}' has no keyframes on field.strength.")

# Sort keyframes by frame
keyframes = sorted(v_fc.keyframe_points, key=lambda kp: kp.co.x)

print(f"Processing {len(keyframes)} keyframes from vortex '{vortex.name}'...")
print(f"Targets: attractive='{attractive.name}', repulsive='{repulsive.name}'")

for kp in keyframes:
    frame = int(round(kp.co.x))

    # Evaluate the vortex strength at this exact frame (respects interpolation)
    v_strength = v_fc.evaluate(frame)
    abs_val = abs(v_strength)

    # Values per your rule
    attractive_val = -1.0 * abs_val
    repulsive_val  =  1.0 * abs_val

    # Set frame (helps ensure consistent context)
    bpy.context.scene.frame_set(frame)

    # Apply and keyframe
    attractive.field.strength = attractive_val
    attractive.keyframe_insert(data_path="field.strength", frame=frame)

    repulsive.field.strength = repulsive_val
    repulsive.keyframe_insert(data_path="field.strength", frame=frame)

    # Console log for this frame
    print(f"Frame {frame}: set 'attractive'={attractive_val:.6f}, 'repulsive'={repulsive_val:.6f}")

print("Done.")
