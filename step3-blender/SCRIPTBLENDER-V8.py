import bpy

EPS = 1e-6  # tolerance for checking "strength == 0"


def find_object_by_name(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        print(f"[WARN] Object named '{name}' not found.")
    return obj


def find_single_vortex():
    for obj in bpy.data.objects:
        if hasattr(obj, "field") and obj.field and obj.field.type == 'VORTEX':
            return obj
    print("[WARN] No VORTEX force object found.")
    return None


def get_fcurve(obj, data_path, array_index=None):
    """Return the fcurve for obj.data_path (optionally array_index)."""
    ad = getattr(obj, "animation_data", None)
    if not ad or not ad.action:
        return None
    for fc in ad.action.fcurves:
        if fc.data_path == data_path and (array_index is None or fc.array_index == array_index):
            return fc
    return None


def has_keyframe_at_frame(obj, data_path, frame, array_index=None, tol=1e-3):
    fc = get_fcurve(obj, data_path, array_index)
    if not fc:
        return False
    for kp in fc.keyframe_points:
        if abs(kp.co[0] - frame) <= tol:
            return True
    return False


def insert_strength_key(obj, frame, value):
    # Set the value at that frame and keyframe it on the ForceFieldSettings block
    obj.field.strength = value
    # Insert on the sub-RNA so the data_path is "strength" (which lands on "field.strength" under the object)
    obj.field.keyframe_insert(data_path="strength", frame=frame)
    print(f"[INFO] Inserted keyframe: {obj.name} | frame {frame} | strength {value}")


def main():
    # Required objects
    inward_a = find_object_by_name("inward-squared-force")
    inward_b = find_object_by_name("inward-squared-negative")
    vortex = find_single_vortex()

    if not (inward_a and inward_b and vortex and hasattr(vortex, "field") and vortex.field):
        print("[ERROR] Missing required force objects or their field settings. Aborting.")
        return

    # Get the vortex strength fcurve (stored on the OBJECT animation data with data_path 'field.strength')
    vortex_fc = get_fcurve(vortex, "field.strength")
    if not vortex_fc:
        print("[WARN] Vortex has no keyframes on strength. Nothing to do.")
        return

    # For every vortex keyframe where strength == 0, ensure the other two have a keyframe at the same frame with strength 0
    for kp in vortex_fc.keyframe_points:
        frame = kp.co[0]
        value = kp.co[1]
        if abs(value) <= EPS:
            # inward A
            if not has_keyframe_at_frame(inward_a, "field.strength", frame):
                insert_strength_key(inward_a, frame, 0.0)
            else:
                print(f"[SKIP] '{inward_a.name}' already has a strength key at frame {frame}")

            # inward B
            if not has_keyframe_at_frame(inward_b, "field.strength", frame):
                insert_strength_key(inward_b, frame, 0.0)
            else:
                print(f"[SKIP] '{inward_b.name}' already has a strength key at frame {frame}")

    print("[DONE] Synchronization complete.")


if __name__ == "__main__":
    main()
