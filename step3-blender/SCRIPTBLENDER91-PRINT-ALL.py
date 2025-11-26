import bpy

# --------------------------- Config ---------------------------
# Extra objects you want to print (in addition to ALL VORTEX fields found).
TARGETS = (
    "attractive",
    "repulsive",
    "inward-squared-force",
    "inward-squared-negative",
    "in-constant",
    "in-constant-negative",
    "in-large",
    "in-large-negative",
    "in-small",
    "in-small-negative",
    "constant-force",
    "constant",
    "constant-negative",
    "small-force",
    "small",
    "small-negative",
    "large-force",
    "large",
    "large-negative",
    "huge",
    "huge-negative"
)

# If True, TARGETS that are not VORTEX will be skipped.
ONLY_VORTEX_FOR_TARGETS = False

# F-Curve data path for force field strength:
DATA_PATH = "field.strength"
# --------------------------------------------------------------


def print_strength_keyframes(obj, require_vortex=False):
    """Print the strength value and frame number for every keyframe on field.strength.
    If require_vortex=True, only run for VORTEX force fields.
    """
    if obj is None:
        print("Object is None.")
        return

    field = getattr(obj, "field", None)
    if field is None:
        print(f'[{obj.name}] has no force field settings; skipping.')
        return

    if require_vortex and field.type != 'VORTEX':
        print(f'[{obj.name}] is not a VORTEX force field; skipping.')
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

    type_suffix = f" | {field.type}" if getattr(field, "type", None) else ""
    for fc in fcurves:
        # Sort by frame to print in chronological order
        kfps = sorted(fc.keyframe_points, key=lambda k: k.co[0])
        for kfp in kfps:
            frame = kfp.co[0]
            value = kfp.co[1]
            print(f'[{obj.name}{type_suffix}] frame {frame:g}: strength {value:.6g}')


def main():
    processed = set()

    # 1) Always scan the whole scene for VORTEX fields (your original behavior).
    found_any_vortex = False
    for obj in bpy.data.objects:
        field = getattr(obj, "field", None)
        if field and field.type == 'VORTEX':
            found_any_vortex = True
            processed.add(obj.name)
            print_strength_keyframes(obj, require_vortex=True)

    if not found_any_vortex:
        print('No VORTEX force fields found in the scene.')

    # 2) Additionally process any explicitly named TARGETS.
    for name in TARGETS:
        if name in processed:
            continue  # avoid duplicate prints if a target was already handled above
        obj = bpy.data.objects.get(name)
        if obj is None:
            print(f'Object "{name}" not found; skipping.')
            continue
        print_strength_keyframes(obj, require_vortex=ONLY_VORTEX_FOR_TARGETS)


if __name__ == "__main__":
    main()
