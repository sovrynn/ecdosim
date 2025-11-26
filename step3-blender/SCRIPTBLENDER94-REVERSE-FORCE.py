import bpy

# ======= CONFIG =======
FORCE_NAME = "NAME"   # <— set this to the exact object name
# ======================


def get_object_by_name(name: str):
    obj = bpy.data.objects.get(name)
    if obj is None:
        print(f"Object named '{name}' not found.")
    return obj


def negate_strength_keyframes(obj: bpy.types.Object):
    """
    For the given force field object, multiply every keyframed value of field.strength by -1.
    Prints: frame number, previous value, new value.
    """
    # Basic checks
    if obj is None:
        return
    if getattr(obj, "field", None) is None:
        print(f"'{obj.name}' has no Force Field settings; aborting.")
        return

    ad = obj.animation_data
    if ad is None or ad.action is None:
        print(f"'{obj.name}' has no animation data/action; nothing to modify.")
        return

    action = ad.action
    # field.strength is the animated data path for force strength
    fcurves = [fc for fc in action.fcurves if fc.data_path == "field.strength"]
    if not fcurves:
        print(f"'{obj.name}' has no keyframes on 'field.strength'; nothing to modify.")
        return

    print(f"Processing force: '{obj.name}' (type: {obj.field.type})")
    total = 0

    for fc in fcurves:
        # Work in chronological order for clearer logs
        for kp in sorted(fc.keyframe_points, key=lambda k: k.co[0]):
            frame = kp.co[0]
            old_val = kp.co[1]
            new_val = -old_val

            # Update the keyframe value
            kp.co[1] = new_val

            # Preserve curve shape: flip handle Y-values as well
            hl = kp.handle_left
            hr = kp.handle_right
            kp.handle_left = (hl[0], -hl[1])
            kp.handle_right = (hr[0], -hr[1])

            print(f"[{obj.name}] frame {int(frame)}: strength {old_val:.6g} -> {new_val:.6g}")
            total += 1

        fc.update()

    if total == 0:
        print("No keyframe points were modified.")
    else:
        print(f"Done. Modified {total} keyframe(s).")


def main():
    obj = get_object_by_name(FORCE_NAME)
    negate_strength_keyframes(obj)


if __name__ == "__main__":
    main()
