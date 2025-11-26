import bpy

TARGETS = ("attractive", "repulsive")
TARGETS = ("inward-squared-force", "inward-squared-negative")
DATA_PATH = "field.strength"

def print_strength_keyframes(obj):
    """Print the strength value and frame number for every keyframe on field.strength."""
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

    # Find the F-Curve(s) that animate the force field strength
    fcurves = [fc for fc in ad.action.fcurves if fc.data_path == DATA_PATH]
    if not fcurves:
        print(f'[{obj.name}] has no keyframes on "{DATA_PATH}"; skipping.')
        return

    for fc in fcurves:
        # Sort by frame to print in chronological order
        kfps = sorted(fc.keyframe_points, key=lambda k: k.co[0])
        for kfp in kfps:
            frame = kfp.co[0]
            value = kfp.co[1]  # the keyed strength value at this frame
            print(f'[{obj.name}] frame {frame:g}: strength {value:.6g}')

def main():
    for name in TARGETS:
        obj = bpy.data.objects.get(name)
        if obj is None:
            print(f'Object "{name}" not found; skipping.')
            continue
        print_strength_keyframes(obj)

if __name__ == "__main__":
    main()
