import bpy

STRENGTH_PATH = "field.strength"
FLOW_PATH = "field.flow"

def print_vortex_strength_and_flow_keyframes(obj):
    """Print strength and flow values for every keyframe on field.strength (for VORTEX force fields)."""
    if obj is None or getattr(obj, "field", None) is None:
        return
    if obj.field.type != 'VORTEX':
        return

    ad = obj.animation_data
    if ad is None or ad.action is None:
        print(f'[{obj.name}] has no animation data/action; skipping.')
        return

    act = ad.action
    strength_fcurves = [fc for fc in act.fcurves if fc.data_path == STRENGTH_PATH]
    flow_fcurves = [fc for fc in act.fcurves if fc.data_path == FLOW_PATH]

    if not strength_fcurves:
        print(f'[{obj.name}] has no keyframes on "{STRENGTH_PATH}"; skipping.')
        return

    flow_fc = flow_fcurves[0] if flow_fcurves else None

    for fc in strength_fcurves:
        # Sort keyframes by frame
        kfps = sorted(fc.keyframe_points, key=lambda k: k.co[0])
        for kfp in kfps:
            frame = kfp.co[0]
            strength_val = kfp.co[1]
            # Evaluate flow value at this frame (use current value if not animated)
            if flow_fc:
                flow_val = flow_fc.evaluate(frame)
            else:
                flow_val = obj.field.flow
            print(f'[{obj.name} | VORTEX] frame {frame:g}: strength {strength_val:.6g}, flow {flow_val:.6g}')

def main():
    found = False
    for obj in bpy.data.objects:
        if getattr(obj, "field", None) and obj.field.type == 'VORTEX':
            found = True
            print_vortex_strength_and_flow_keyframes(obj)
    if not found:
        print('No VORTEX force fields found in the scene.')

if __name__ == "__main__":
    main()
