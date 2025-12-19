import bpy

def find_vortex_object(name="Vortex"):
    # Prefer an object with this name that has a FORCE field
    obj = bpy.data.objects.get(name)
    if obj and obj.field and obj.field.type == 'VORTEX':
        return obj

    # Fallback: search all objects for a VORTEX field with the given name
    for o in bpy.data.objects:
        if o.name == name and o.field and o.field.type == 'VORTEX':
            return o
    return None

def get_fcurve(obj, data_path, index=None):
    ad = getattr(obj, "animation_data", None)
    act = getattr(ad, "action", None) if ad else None
    if not act:
        return None
    for fc in act.fcurves:
        if fc.data_path == data_path and (index is None or fc.array_index == index):
            return fc
    return None

def keyframes_union_frames(*fcurves):
    frames = set()
    for fc in fcurves:
        if not fc:
            continue
        for kp in fc.keyframe_points:
            # kp.co.x is the frame number (float). Round to nearest int frame.
            frames.add(int(round(kp.co.x)))
    return sorted(frames)

def eval_fcurve_or_current(fc, frame, current_value):
    if fc:
        return float(fc.evaluate(frame))
    return float(current_value)

def main():
    obj = find_vortex_object("Vortex")
    if not obj:
        print('ERROR: No VORTEX force field object named "Vortex" found.')
        return

    # Strength is on the field settings
    strength_path = "field.strength"

    # Flow is most commonly driven by the Wind field ("field.flow").
    # Vortex fields typically don't have a "flow" setting, but the user requested it,
    # so we try "field.flow" first; if not present, we fall back to 0.0.
    flow_path = "field.flow"

    strength_fc = get_fcurve(obj, strength_path)
    flow_fc = get_fcurve(obj, flow_path)

    frames = keyframes_union_frames(strength_fc, flow_fc)

    # If there are no keyframes on those properties, do nothing (or print nothing).
    if not frames:
        print("")  # single line as requested
        return

    # Current values (fallback if a property isn't keyed)
    strength_current = getattr(obj.field, "strength", 0.0)

    # Only some force fields have "flow". If missing, treat as 0.0.
    flow_current = getattr(obj.field, "flow", 0.0) if hasattr(obj.field, "flow") else 0.0

    parts = []
    for fr in frames:
        strength_val = eval_fcurve_or_current(strength_fc, fr, strength_current)
        flow_val = eval_fcurve_or_current(flow_fc, fr, flow_current)

        # "X Y Z " => frame strength flow
        parts.extend([str(fr), str(strength_val), str(flow_val)])

    print(" ".join(parts))

if __name__ == "__main__":
    main()
