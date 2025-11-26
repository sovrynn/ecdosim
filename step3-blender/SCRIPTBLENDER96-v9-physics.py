import bpy

# Choose the exact object names you want to process:
TARGETS = ("inward-squared-force", "inward-squared-negative")
# Or use this alternative set (comment one out as needed):
TARGETS = ("in-constant", "in-constant-negative", "in-large", "in-large-negative", "in-small", "in-small-negative")

DATA_PATH = "field.strength"  # matches your script's fcurve filtering

def backfill_strength_keyframes(obj):
    """
    For each keyframe i >= 3rd (index >= 2 by frame order), set value(i) = value(i-1).
    Do it BACKWARDS to avoid overwriting values we still need.
    Only operates on Blender's basic 'FORCE' type (attractive/repulsive).
    Logs all modified keyframes as: [name] frame N: strength old -> new
    """
    if obj is None:
        print("Object is None.")
        return
    if not hasattr(obj, "field") or obj.field is None:
        print(f'[{obj.name}] has no force field settings; skipping.')
        return
    if obj.field.type != 'FORCE':
        print(f'[{obj.name}] field type is "{obj.field.type}", not basic FORCE; skipping.')
        return

    ad = obj.animation_data
    if ad is None or ad.action is None:
        print(f'[{obj.name}] has no animation data/action; skipping.')
        return

    # Find FCurves for the force strength on this object (matches your pattern)
    fcurves = [fc for fc in ad.action.fcurves if fc.data_path == DATA_PATH]
    if not fcurves:
        print(f'[{obj.name}] has no keyframes on "{DATA_PATH}"; skipping.')
        return

    for fc in fcurves:
        # Sort keyframes by frame index safely
        kps = list(fc.keyframe_points)
        if len(kps) < 3:
            print(f'[{obj.name}] has < 3 keyframes on "{DATA_PATH}"; nothing to modify.')
            continue

        # Sort by frame (ascending) without mutating original order assumptions
        kps.sort(key=lambda k: k.co[0])

        # Walk backwards: last -> index 2 (inclusive)
        # For each i, set value(i) = value(i-1)
        for i in range(len(kps) - 1, 1, -1):
            prev = kps[i - 1]
            curr = kps[i]

            prev_val = float(prev.co[1])
            old_val = float(curr.co[1])

            # Copy the value
            curr.co[1] = prev_val

            # Keep the curve visually consistent:
            # align handle Y to the new (copied) value, keep X positions intact
            try:
                curr.handle_left[1]  = prev_val
                curr.handle_right[1] = prev_val
            except Exception:
                # If handle access isn't available in the current context/version, ignore gracefully
                pass

            print(f'[{obj.name}] frame {curr.co[0]:g}: strength {old_val:.6g} -> {prev_val:.6g}')

        # Notify Blender that we updated this curve
        try:
            fc.update()
        except Exception:
            try:
                fc.keyframe_points.update()
            except Exception:
                pass

def main():
    for name in TARGETS:
        obj = bpy.data.objects.get(name)
        if obj is None:
            print(f'Object "{name}" not found; skipping.')
            continue
        backfill_strength_keyframes(obj)

if __name__ == "__main__":
    main()
