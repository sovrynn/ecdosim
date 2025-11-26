import bpy

DATA_PATH = "field.strength"

def print_vortex_strength_keyframes(obj):
    """Print the strength value and frame number for every keyframe on field.strength (VORTEX only)."""
    if obj is None or getattr(obj, "field", None) is None:
        return
    if obj.field.type != 'VORTEX':
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
        # Sort by frame so output is chronological
        kfps = sorted(fc.keyframe_points, key=lambda k: k.co[0])
        for kfp in kfps:
            frame = kfp.co[0]
            value = kfp.co[1]
            print(f'[{obj.name} | VORTEX] frame {frame:g}: strength {value:.6g}')

def main():
    found = False
    for obj in bpy.data.objects:
        if getattr(obj, "field", None) and obj.field.type == 'VORTEX':
            found = True
            print_vortex_strength_keyframes(obj)
    if not found:
        print('No VORTEX force fields found in the scene.')

if __name__ == "__main__":
    main()
