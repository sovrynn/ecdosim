import bpy

# ----------------------------
# Parameters (edit as needed)
# ----------------------------
# The two "basic" force fields to drive:
TARGETS = ("inward-squared-force", "inward-squared-negative")

# Data path for force field strength:
DATA_PATH = "field.strength"

# If you prefer to pick a specific vortex by name, set VORTEX_NAME to a string.
# Leave as None to auto-detect exactly one vortex in the scene.
VORTEX_NAME = None


# ----------------------------
# Utilities
# ----------------------------
def get_object_by_name(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        print(f'Object "{name}" not found; skipping.')
    return obj


def ensure_force_field(obj):
    if obj is None:
        return False
    if not hasattr(obj, "field") or obj.field is None:
        print(f'[{obj.name}] has no force field settings; skipping.')
        return False
    return True


def get_strength_fcurve(obj):
    """Return the F-Curve controlling field.strength, or None if missing."""
    ad = obj.animation_data
    if ad is None or ad.action is None:
        return None
    for fc in ad.action.fcurves:
        if fc.data_path == DATA_PATH:
            return fc
    return None


def get_sorted_keyframes(fc):
    """Return a sorted list of (frame, value) pairs from an F-Curve's keyframe points."""
    if fc is None:
        return []
    pts = [(int(round(k.co[0])), float(k.co[1])) for k in fc.keyframe_points]
    pts.sort(key=lambda kv: kv[0])
    return pts


def set_keyframe_strength(obj, frame, value, log=True):
    """
    Set the object's field.strength to value at a specific frame and insert a keyframe.
    Only touches that one frame. Prints a concise log line.
    """
    if obj is None:
        return
    # Temporarily set the property and insert a keyframe at 'frame'
    obj.field.strength = value
    obj.keyframe_insert(data_path=DATA_PATH, frame=frame)
    if log:
        print(f'[{obj.name}] frame {frame}: strength {value:.6g}')


def find_single_vortex():
    """
    Return exactly one vortex object:
     - If VORTEX_NAME is set, use that object (ensure it is a VORTEX).
     - Otherwise, auto-detect exactly one object with field.type == 'VORTEX'.
    """
    if VORTEX_NAME:
        obj = bpy.data.objects.get(VORTEX_NAME)
        if obj and ensure_force_field(obj) and getattr(obj.field, "type", None) == 'VORTEX':
            return obj
        else:
            print(f'Vortex "{VORTEX_NAME}" not found or not a VORTEX field.')
            return None

    vortices = []
    for obj in bpy.data.objects:
        if ensure_force_field(obj) and getattr(obj.field, "type", None) == 'VORTEX':
            vortices.append(obj)

    if len(vortices) == 0:
        print("No VORTEX force field found.")
        return None
    if len(vortices) > 1:
        print("Multiple VORTEX force fields found; please set VORTEX_NAME to pick one.")
        return None
    return vortices[0]


# ----------------------------
# Core logic
# ----------------------------
def drive_targets_from_vortex(vortex_obj, target_names):
    # Get vortex strength curve and its keyframes
    fc_vortex = get_strength_fcurve(vortex_obj)
    if fc_vortex is None:
        print(f'[{vortex_obj.name}] has no keyframes on "{DATA_PATH}"; nothing to do.')
        return

    vortex_keys = get_sorted_keyframes(fc_vortex)
    if not vortex_keys:
        print(f'[{vortex_obj.name}] has no keyframes to process.')
        return

    # Resolve target objects
    targets = []
    for name in target_names:
        obj = get_object_by_name(name)
        if obj and ensure_force_field(obj):
            # Optional: check that they're "basic" force fields
            # (Blender uses 'FORCE' for the simple force field type)
            ftype = getattr(obj.field, "type", None)
            if ftype not in (None, 'FORCE'):
                print(f'[{obj.name}] is type "{ftype}", not basic FORCE; continuing anyway.')
            targets.append(obj)

    if len(targets) != len(target_names):
        print("Some target objects were missing; continuing with those found.")

    if not targets:
        print("No valid target force fields found; aborting.")
        return

    # Process each non-zero keyframe k on the vortex,
    # and act on the next keyframe k_next (if it exists).
    # For each such k:
    #  - Set both targets at frame k to 0
    #  - Set target[0] at k_next to -abs(v_k)
    #  - Set target[1] at k_next to +abs(v_k)
    # Print every modified keyframe line as we create it.

    # Map targets so we can assign signs deterministically:
    if len(targets) >= 2:
        t_neg = targets[0]  # will receive -abs(v)
        t_pos = targets[1]  # will receive +abs(v)
    else:
        # If only one target present, we still set it to 0 at k and -abs(v) at k_next
        t_neg = targets[0]
        t_pos = None

    # Iterate over vortex keyframes, tracking the "next" one
    for i, (k_frame, k_value) in enumerate(vortex_keys):
        # Skip zero-strength keys
        if abs(k_value) == 0.0:
            continue

        # Find the next vortex keyframe (if any)
        if i + 1 >= len(vortex_keys):
            # No next keyframe to target for k+1 step; skip the second part
            next_frame = None
        else:
            next_frame = vortex_keys[i + 1][0]

        # 1) At frame k: set both targets to 0
        for tgt in targets:
            set_keyframe_strength(tgt, k_frame, 0.0, log=True)

        # 2) At frame k_next: set signs based on abs(k_value), if next exists
        if next_frame is not None:
            v_abs = abs(k_value)
            set_keyframe_strength(t_neg, next_frame, -v_abs, log=True)
            if t_pos is not None:
                set_keyframe_strength(t_pos, next_frame, +v_abs, log=True)


def main():
    # Find the vortex
    vortex = find_single_vortex()
    if vortex is None:
        return

    print(f'Using VORTEX: "{vortex.name}"')

    # Run the driving logic
    drive_targets_from_vortex(vortex, TARGETS)

    # Nudge the depsgraph by updating scenes (helps UI reflect fresh keyframes)
    for area in bpy.context.screen.areas:
        if area.type == 'GRAPH_EDITOR':
            area.tag_redraw()
    bpy.context.view_layer.update()


if __name__ == "__main__":
    main()
