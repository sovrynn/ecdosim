import bpy

# ======== CONFIG ========
SCALE = 0.67  # <— change this to the multiplier you want
# ========================


def find_first_vortex_object():
    for obj in bpy.data.objects:
        # Objects with force fields have a .field (FieldSettings) attr
        if hasattr(obj, "field") and obj.field is not None:
            try:
                if obj.field.type == 'VORTEX':
                    return obj
            except Exception:
                # In case some linked/library object has odd access issues
                continue
    return None


def scale_keyframes_on_fcurve(fcurve, label):
    """
    Scales the Y values of all keyframe points (and their handles) on this fcurve.
    Prints old/new values with frame numbers.
    """
    if fcurve is None or not fcurve.keyframe_points:
        return 0

    count = 0
    for kp in fcurve.keyframe_points:
        frame = kp.co[0]
        old_val = kp.co[1]
        new_val = old_val * SCALE

        # Update the keyframe value
        kp.co[1] = new_val

        # Keep interpolation shape consistent by scaling handle Y values too
        # (handles exist even for vector/stepped but updating Y is safe)
        hl = kp.handle_left
        hr = kp.handle_right
        kp.handle_left   = (hl[0], hl[1] * SCALE)
        kp.handle_right  = (hr[0], hr[1] * SCALE)

        print(f"[Frame {int(frame)}] {label}: {old_val:.6g} -> {new_val:.6g}")
        count += 1

    # Let Blender know we changed keyframes
    fcurve.update()
    return count


def main():
    obj = find_first_vortex_object()
    if obj is None:
        print("No Vortex force field found in the scene.")
        return

    print(f"Vortex force field object: '{obj.name}'")
    ad = obj.animation_data
    if ad is None or ad.action is None:
        print("This Vortex has no action / keyframes. Nothing to scale.")
        return

    # Find fcurves for the properties we care about
    act = ad.action
    strength_fc = None
    flow_fc = None
    for fc in act.fcurves:
        if fc.data_path == "field.strength":
            strength_fc = fc
        elif fc.data_path == "field.flow":
            flow_fc = fc

    if strength_fc is None and flow_fc is None:
        print("No keyframes found for 'strength' or 'flow' on this Vortex.")
        return

    # Scale and report
    total = 0
    total += scale_keyframes_on_fcurve(strength_fc, "strength") if strength_fc else 0
    total += scale_keyframes_on_fcurve(flow_fc, "flow") if flow_fc else 0

    print(f"Done. Scaled {total} keyframe(s) by SCALE={SCALE}.")


if __name__ == "__main__":
    main()
