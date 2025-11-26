import bpy

# =========================
# Configuration (edit these)
# =========================
INWARD_NEG_NAME = "inward-squared-force"      # will get +running_sum
INWARD_POS_NAME = "inward-squared-negative"   # will get -running_sum

# If you want to target a specific vortex object by name, put it here.
# Leave as None to auto-detect the first object with a VORTEX field.
VORTEX_NAME = None

# =========================
# Helpers
# =========================
def get_force_obj_by_name(name: str):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Object named '{name}' not found.")
    if not hasattr(obj, "field") or obj.field is None:
        raise RuntimeError(f"Object '{name}' does not have a Force Field physics.")
    return obj

def get_vortex_obj(vortex_name=None):
    if vortex_name:
        obj = get_force_obj_by_name(vortex_name)
        if obj.field.type != 'VORTEX':
            raise RuntimeError(f"Object '{vortex_name}' is not a VORTEX field (found {obj.field.type}).")
        return obj
    # Fallback: first object with a VORTEX field
    for obj in bpy.data.objects:
        if hasattr(obj, "field") and obj.field and obj.field.type == 'VORTEX':
            return obj
    raise RuntimeError("No object with a VORTEX force field found.")

def get_strength_fcurve(obj):
    ad = obj.animation_data
    if ad is None or ad.action is None:
        raise RuntimeError(f"Object '{obj.name}' has no animation data/action on which to read keyframes.")
    for fc in ad.action.fcurves:
        if fc.data_path == "field.strength":
            return fc
    raise RuntimeError(f"Object '{obj.name}' has no FCurve for field.strength.")

def sorted_keyframes_points(fcurve):
    # Return keyframe points sorted by frame x
    return sorted(fcurve.keyframe_points, key=lambda kp: kp.co.x)

def insert_strength_key(obj, frame: int, value: float):
    obj.field.strength = value
    obj.keyframe_insert(data_path="field.strength", frame=frame)

# =========================
# Main
# =========================
def main():
    inward_pos = get_force_obj_by_name(INWARD_POS_NAME)
    inward_neg = get_force_obj_by_name(INWARD_NEG_NAME)
    vortex = get_vortex_obj(VORTEX_NAME)

    v_fc = get_strength_fcurve(vortex)
    kps = sorted_keyframes_points(v_fc)
    if not kps:
        raise RuntimeError(f"Vortex '{vortex.name}' has no keyframes on strength.")

    # We will:
    # - NOT modify the first keyframe (whatever/wherever it is)
    # - For each subsequent key where value != 0, compute:
    #   running_sum += (value_at_key) * (frame_at_key - frame_of_previous_zero_key)
    # Assumption per your spec: the previous keyframe to each non-zero is a zero-strength keyframe.
    running_sum = 0.0

    # Track last zero keyframe (frame number as int)
    # Initialize it from the first key if its value is 0, else None until we see a zero.
    # The spec says the first one is zero, but we’ll handle it defensively.
    first_kp = kps[0]
    first_frame = int(round(first_kp.co.x))
    first_val = float(first_kp.co.y)

    last_zero_frame = first_frame if abs(first_val) < 1e-12 else None

    # We'll collect logs to print cleanly at the end, grouped by force.
    log_pos = []  # (frame, value)
    log_neg = []  # (frame, value)

    # Iterate from the SECOND keyframe onward (skip index 0).
    for i in range(1, len(kps)):
        kp = kps[i]
        frame_i = int(round(kp.co.x))
        val_i = float(kp.co.y)

        # Update tracker when we pass a zero keyframe
        if abs(val_i) < 1e-12:
            last_zero_frame = frame_i
            continue  # zero keys themselves don't trigger writes

        # Non-zero keyframe: per spec, previous keyframe should be zero-strength.
        # We compute distance from the *previous zero* keyframe.
        if last_zero_frame is None:
            # Defensive: if we haven't encountered a zero yet, try to use the previous keyframe
            prev_kp = kps[i - 1]
            last_zero_frame = int(round(prev_kp.co.x))
            # (If that prev was also non-zero, we still proceed with this distance.)

        frame_dist = frame_i - last_zero_frame
        # Multiply and accumulate
        running_sum += (val_i * frame_dist)

        # At this non-zero keyframe frame, set keyframes on the two inward forces
        insert_strength_key(inward_pos, frame_i, running_sum)   # +running_sum
        insert_strength_key(inward_neg, frame_i, -running_sum)  # -running_sum

        log_pos.append((frame_i, running_sum))
        log_neg.append((frame_i, -running_sum))

    # Print logs as requested
    print("\n=== Modified keyframes for '{}' (positive) ===".format(inward_pos.name))
    if log_pos:
        for f, v in log_pos:
            print(f"Frame {f}: strength {v}")
    else:
        print("(No keyframes inserted)")

    print("\n=== Modified keyframes for '{}' (negative) ===".format(inward_neg.name))
    if log_neg:
        for f, v in log_neg:
            print(f"Frame {f}: strength {v}")
    else:
        print("(No keyframes inserted)")

# Run it
if __name__ == "__main__":
    main()
