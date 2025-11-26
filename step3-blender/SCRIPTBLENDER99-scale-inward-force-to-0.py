import bpy

# ----------------------------
# Parameters (edit as needed)
# ----------------------------
FORCE_OBJECT_NAMES = [
    "inward-squared-force",
    "inward-squared-negative",
]

# If True, also scale the keyframe handles' Y values to keep curve shape
SCALE_HANDLES = True

# ----------------------------
# Helpers
# ----------------------------
def find_strength_fcurve(obj):
    """Return the F-Curve for field.strength on the given object, or None."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return None
    for fc in ad.action.fcurves:
        if fc.data_path == "field.strength":
            return fc
    return None

def format_num(x):
    return f"{x:.6g}"

# ----------------------------
# Main
# ----------------------------
for name in FORCE_OBJECT_NAMES:
    obj = bpy.data.objects.get(name)
    if obj is None:
        print(f"[WARN] Object '{name}' not found; skipping.")
        continue

    # Ensure it actually has force-field settings
    if not hasattr(obj, "field") or obj.field is None:
        print(f"[WARN] Object '{name}' has no force-field settings; skipping.")
        continue

    fc = find_strength_fcurve(obj)
    if fc is None or len(fc.keyframe_points) < 3:
        print(f"[WARN] Object '{name}' needs at least 3 keyframes on field.strength; skipping.")
        continue

    # Sort keyframes by frame (X)
    kfs = sorted(fc.keyframe_points, key=lambda k: k.co.x)

    second_kf = kfs[1]
    last_kf   = kfs[-1]

    second_frame = float(second_kf.co.x)
    last_frame   = float(last_kf.co.x)

    denom = (last_frame - second_frame)
    if abs(denom) < 1e-12:
        print(f"[WARN] Object '{name}': second and last keyframes share the same frame ({second_frame}); cannot compute scaling.")
        continue

    print(f"\n[INFO] Processing '{name}'")
    print(f"       second_frame={format_num(second_frame)}, last_frame={format_num(last_frame)}")

    # Modify from the third keyframe onward (index >= 2 after sorting)
    for kf in kfs[2:]:
        frame = float(kf.co.x)
        # Scale factor: 1 - (frame - second_frame) / (last_frame - second_frame)
        factor = 1.0 - (frame - second_frame) / denom
        # (Optional) clamp if someone put a keyframe past the last
        # factor = max(min(factor, 1.0), -1e6)

        old_y = float(kf.co.y)
        new_y = old_y * factor
        kf.co.y = new_y

        if SCALE_HANDLES:
            # scale Y of handles too to preserve local curve shape
            hlx, hly = kf.handle_left
            hrx, hry = kf.handle_right
            kf.handle_left  = (hlx,  hly * factor)
            kf.handle_right = (hrx,  hry * factor)

        print(f"  frame={int(round(frame))}  strength={format_num(new_y)}  (factor={format_num(factor)})")

    # Let Blender know we changed animation data
    fc.update()

# Optional: refresh the depsgraph so viewport reflects changes immediately
for area in bpy.context.screen.areas:
    if area.type == 'GRAPH_EDITOR' or area.type == 'DOPESHEET_EDITOR' or area.type == 'VIEW_3D':
        area.tag_redraw()
