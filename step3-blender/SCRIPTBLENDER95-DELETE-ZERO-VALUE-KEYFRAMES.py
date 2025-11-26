import bpy

# ==============================
# CONFIGURE YOUR FORCE NAMES HERE
# ==============================
FORCE_NAMES = [
    # "attractive",
    # "repulsive",
    # "inward-squared-force",
    # "inward-squared-negative",
    "in-constant",
    "in-constant-negative",
    "in-large",
    "in-large-negative",
    "in-small",
    "in-small-negative",
]

# Treat very small values as zero (helps avoid float precision issues)
EPS = 1e-6

def get_strength_fcurve(obj):
    """Return the FCurve for field.strength on the given object, or None."""
    if not obj or not obj.animation_data or not obj.animation_data.action:
        return None
    for fcu in obj.animation_data.action.fcurves:
        if fcu.data_path == "field.strength":
            return fcu
    return None

def delete_zero_strength_keyframes_except_ends(obj):
    """Delete all zero-strength keyframes except the first and last (by frame)."""
    if not hasattr(obj, "field") or obj.field is None:
        return 0
    if obj.field.type != 'FORCE':  # Basic attractive/repulsive field
        return 0

    fcu = get_strength_fcurve(obj)
    if fcu is None or len(fcu.keyframe_points) < 3:
        return 0

    kps = list(fcu.keyframe_points)
    # Order keyframes by frame (co.x)
    order = sorted(range(len(kps)), key=lambda i: kps[i].co.x)

    # Indices (into original fcurve.keyframe_points) of first and last keyframes by frame order
    first_i = order[0]
    last_i  = order[-1]

    # Collect indices to delete (skip the first and last)
    to_delete = []
    for i in order[1:-1]:
        val = kps[i].co.y
        if abs(val) <= EPS:
            to_delete.append(i)

    # Remove from highest index to lowest so indices remain valid
    deleted = 0
    for i in sorted(to_delete, reverse=True):
        frame_num = int(round(kps[i].co.x))
        print(f"[Deleted] Force '{obj.name}' — frame {frame_num} (strength=0)")
        fcu.keyframe_points.remove(kps[i])
        deleted += 1

    # Update the fcurve after edits
    if deleted:
        fcu.update()

    return deleted

def main(force_names):
    if not force_names:
        print("No force names provided in FORCE_NAMES. Add names and re-run.")
        return

    # Resolve objects by exact name
    targets = []
    for nm in force_names:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            print(f"[Skip] No object named '{nm}' found.")
        else:
            targets.append(ob)

    total_deleted = 0
    for ob in targets:
        deleted = delete_zero_strength_keyframes_except_ends(ob)
        if deleted == 0:
            print(f"[Info] Force '{ob.name}': nothing to delete (or not a basic Force field, or fewer than 3 keyframes).")
        total_deleted += deleted

    print(f"[Done] Total keyframes deleted: {total_deleted}")

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    main(FORCE_NAMES)
