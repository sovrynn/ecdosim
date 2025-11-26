import bpy

TARGETS = ("inward-squared-force", "inward-squared-negative")
TARGETS = ("in-constant", "in-constant-negative", "in-large", "in-large-negative", "in-small", "in-small-negative")
TARGETS = ("constant", "constant-negative", "large", "large-negative", "small", "small-negative", "huge", "huge-negative")
FACTOR = 0.67
DATA_PATH = "field.strength"

def scale_strength_keyframes(obj, factor):
    """Multiply the strength value at every keyframe by `factor` and log each change."""
    if obj is None:
        print("Object is None.")
        return
    if not hasattr(obj, "field") or obj.field is None:
        print(f'[{obj.name}] has no force field settings; skipping.')
        return
    ad = obj.animation_data
    if ad is None or ad.action is None:
        print(f'[{obj.name}] has no animation data/action; skipping.')
        return

    # Find the F-Curve that controls the force field strength
    fcurves = [fc for fc in ad.action.fcurves if fc.data_path == DATA_PATH]
    if not fcurves:
        print(f'[{obj.name}] has no keyframes on "{DATA_PATH}"; skipping.')
        return

    for fc in fcurves:
        for kfp in fc.keyframe_points:
            frame = kfp.co[0]
            old_val = kfp.co[1]
            new_val = old_val * factor

            # Scale the keyframe value
            kfp.co[1] = new_val

            # Scale handles to preserve curve shape proportionally
            kfp.handle_left[1] *= factor
            kfp.handle_right[1] *= factor

            print(f'[{obj.name}] frame {frame:g}: strength {old_val:.6g} -> {new_val:.6g}')

        # Let Blender know we updated the curve
        fc.update()

def main():
    for name in TARGETS:
        obj = bpy.data.objects.get(name)
        if obj is None:
            print(f'Object "{name}" not found; skipping.')
            continue
        scale_strength_keyframes(obj, FACTOR)

if __name__ == "__main__":
    main()
