# Blender Python script
# Scales keyframed values for specified force fields.
# - Plain force fields named:
#     "inward-squared-force" and "inward-squared-negative"
#   -> scales their Strength at every keyframe by SCALE.
# - All Vortex force fields in the scene
#   -> scales their Strength and Flow at every keyframe by SCALE.
#
# For each edited keyframe, prints: object, property, frame, old -> new.
#
# Usage:
#   - Paste into the Text Editor in Blender and Run Script.
#   - Optionally change SCALE below.

import bpy

# ================== Configuration ==================
SCALE = 0.9  # Change if needed
PLAIN_FORCE_NAMES = {"inward-squared-force", "inward-squared-negative"}
# ===================================================

def iter_object_actions(obj):
    """Yield all Actions that can influence the object (active + NLA strip actions)."""
    ad = obj.animation_data
    if not ad:
        return
    if ad.action:
        yield ad.action
    if getattr(ad, "nla_tracks", None):
        for tr in ad.nla_tracks:
            for strip in tr.strips:
                if strip.action:
                    yield strip.action

def find_fcurves(obj, data_path):
    """Collect all FCurves on this object matching a given data_path across actions/NLA."""
    fcurves = []
    for act in iter_object_actions(obj) or []:
        for fc in act.fcurves:
            if fc.data_path == data_path:
                fcurves.append(fc)
    return fcurves

def scale_fcurve_keyframes(obj, fcurve, prop_label, scale):
    """Scale all keyframe Y values (and their handles) of the given FCurve.
       Prints before/after for each keyframe."""
    # Defensive: skip if no keyframes
    if not fcurve.keyframe_points:
        return 0

    count = 0
    for kp in fcurve.keyframe_points:
        frame = kp.co[0]
        old_val = kp.co[1]
        new_val = old_val * scale

        # Scale the keyframe value
        kp.co[1] = new_val

        # Scale handles to preserve curve shape (y only)
        if kp.handle_left:
            kp.handle_left[1] *= scale
        if kp.handle_right:
            kp.handle_right[1] *= scale

        print(f"[{obj.name}] {prop_label} @ frame {int(frame)}: {old_val:.6g} -> {new_val:.6g}")
        count += 1

    # Let Blender recalc tangents
    fcurve.update()
    return count

def process_plain_force(obj, scale):
    """Scale Strength keyframes for a plain force field object."""
    # Only operate on true 'Plain Force' types to be safe
    if not getattr(obj, "field", None) or obj.field.type != 'FORCE':
        return 0
    fcurves = find_fcurves(obj, "field.strength")
    changed = 0
    for fc in fcurves:
        changed += scale_fcurve_keyframes(obj, fc, "Strength", scale)
    return changed

def process_vortex_force(obj, scale):
    """Scale Strength and Flow keyframes for a vortex force field object."""
    if not getattr(obj, "field", None) or obj.field.type != 'VORTEX':
        return 0
    changed = 0
    # Strength
    for fc in find_fcurves(obj, "field.strength"):
        changed += scale_fcurve_keyframes(obj, fc, "Strength", scale)
    # Flow
    for fc in find_fcurves(obj, "field.flow"):
        changed += scale_fcurve_keyframes(obj, fc, "Flow", scale)
    return changed

def main(scale=SCALE):
    total_changes = 0

    # 1) Handle the two named plain force fields (if present)
    for name in PLAIN_FORCE_NAMES:
        obj = bpy.data.objects.get(name)
        if obj is None:
            print(f"[WARN] Plain force named '{name}' not found; skipping.")
            continue
        changes = process_plain_force(obj, scale)
        if changes == 0:
            print(f"[INFO] '{name}' has no keyframes on Strength or no matching FCurves.")
        total_changes += changes

    # 2) Handle ALL vortex force fields present in the scene
    vortex_objs = [o for o in bpy.data.objects
                   if getattr(o, "field", None) and o.field.type == 'VORTEX']
    if not vortex_objs:
        print("[WARN] No Vortex force fields found.")
    for obj in vortex_objs:
        changes = process_vortex_force(obj, scale)
        if changes == 0:
            print(f"[INFO] '{obj.name}' (Vortex) has no keyframes on Strength/Flow or no matching FCurves.")
        total_changes += changes

    print(f"[DONE] Scaled keyframes by factor {scale}. Total keyframes modified: {total_changes}")

if __name__ == "__main__":
    main()
