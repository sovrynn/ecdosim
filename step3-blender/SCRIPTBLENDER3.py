import bpy

EPS = 1e-8  # tolerance to treat tiny values as zero

def find_vortex():
    vortices = [o for o in bpy.data.objects
                if getattr(o, "field", None) and o.field.type == 'VORTEX']
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

# ---- Locate required objects ----
vortex = find_vortex()
attractive = require_force_named("attractive")
repulsive = require_force_named("repulsive")

# ---- Get sorted keyframes from the vortex's strength curve ----
v_fc = get_strength_fcurve(vortex)
if not v_fc or not v_fc.keyframe_points:
    raise RuntimeError(f"Vortex '{vortex.name}' has no keyframes on field.strength.")

keyframes = sorted(v_fc.keyframe_points, key=lambda kp: kp.co.x)

print(f"Processing conditional keyframes from vortex '{vortex.name}'...")
print(f"Targets: attractive='{attractive.name}', repulsive='{repulsive.name}'")

# ---- Process the first keyframe (always), then every other *nonzero* keyframe ----
# We count only nonzero-strength keyframes (after the first) to decide "every other".
# Zero-strength keyframes do not affect the alternation.
first_kp = keyframes[0]
first_frame = int(round(first_kp.co.x))
bpy.context.scene.frame_set(first_frame)
first_strength = v_fc.evaluate(first_frame)
first_abs = abs(first_strength)

# Apply first keyframe regardless of value
attractive.field.strength = -first_abs
attractive.keyframe_insert(data_path="field.strength", frame=first_frame)
repulsive.field.strength = first_abs
repulsive.keyframe_insert(data_path="field.strength", frame=first_frame)
print(f"Frame {first_frame}: set 'attractive'={-first_abs:.6f}, 'repulsive'={first_abs:.6f}")

# Track how many *nonzero* vortex keyframes we've seen AFTER the first one
nonzero_seen = 0
if abs(first_strength) > EPS:
    nonzero_seen = 1  # first was nonzero; start alternation count from 1

for kp in keyframes[1:]:
    frame = int(round(kp.co.x))
    v_strength = v_fc.evaluate(frame)
    a = abs(v_strength)

    # Skip zero-strength keyframes entirely (do not affect alternation)
    if a <= EPS:
        continue

    # For nonzero ones: process every other (i.e., when count is even: 0,2,4,...) AFTER the first
    if nonzero_seen % 2 == 0:
        bpy.context.scene.frame_set(frame)

        attractive_val = -a
        repulsive_val = a

        attractive.field.strength = attractive_val
        attractive.keyframe_insert(data_path="field.strength", frame=frame)

        repulsive.field.strength = repulsive_val
        repulsive.keyframe_insert(data_path="field.strength", frame=frame)

        print(f"Frame {frame}: set 'attractive'={attractive_val:.6f}, 'repulsive'={repulsive_val:.6f}")

    # Increment after handling alternation logic
    nonzero_seen += 1

print("Done.")
