import bpy

# ------------------------------------------------------------
# PARAMETER: space-separated numbers in groups of 3:
#   frame strength flow
# Supports scientific/e notation (e.g. -7.76e-05)
# ------------------------------------------------------------
KEY_DATA = """1 0.0 0.0 15 -0.12653827667236328 0.12700800597667694 19 -0.011920936405658722 0.12700800597667694 24 0.04233600199222565 0.04233600199222565 29 -0.004027361050248146 0.042101550847291946 34 -0.025343086570501328 0.025582192465662956 40 -0.0005026236176490784 0.025401601567864418 46 0.012685844674706459 0.01293011475354433 52 -0.001073333085514605 0.12536683678627014 57 -0.008432144299149513 0.009731337428092957 63 -0.00016754213720560074 0.008467198349535465 69 0.00422889506444335 0.004233600106090307 75 -0.00039108924102038145 0.004221877083182335 80 -0.003370648017153144 0.0033959096763283014 86 -7.767998613417149e-05 0.003386880038306117 92 0.002537168562412262 0.002540159970521927 98 -0.00021466676844283938 0.002528437413275242 103 -0.0016864292556419969 0.0017024694243445992 109 -3.3508287742733955e-05 0.0016934400191530585 115 0.0008450213936157525 0.0008467200095765293 121 0.0 0.0008465690189041197 172 0.0 1.157168298959732e-07"""


def find_vortex_object(name="Vortex"):
    obj = bpy.data.objects.get(name)
    if obj and getattr(obj, "field", None) and obj.field.type == 'VORTEX':
        return obj
    for o in bpy.data.objects:
        if o.name == name and getattr(o, "field", None) and o.field.type == 'VORTEX':
            return o
    return None


def ensure_action(obj):
    obj.animation_data_create()
    if obj.animation_data.action is None:
        obj.animation_data.action = bpy.data.actions.new(name=f"{obj.name}_Action")
    return obj.animation_data.action


def remove_fcurves(action, data_paths):
    to_remove = [fc for fc in action.fcurves if fc.data_path in data_paths]
    for fc in to_remove:
        action.fcurves.remove(fc)


def parse_key_data(s):
    # float(...) already supports scientific notation like -7.76e-05
    toks = s.split()
    if len(toks) % 3 != 0:
        raise ValueError(f"KEY_DATA must have a multiple of 3 numbers, got {len(toks)}")
    triples = []
    for i in range(0, len(toks), 3):
        frame = int(round(float(toks[i])))
        strength = float(toks[i + 1])
        flow = float(toks[i + 2])
        triples.append((frame, strength, flow))
    return triples


def main(key_data_str):
    obj = find_vortex_object("Vortex")
    if not obj:
        print('ERROR: No VORTEX force field object named "Vortex" found.')
        return

    field = obj.field
    strength_path = "field.strength"
    flow_path = "field.flow"  # may not exist for Vortex in some Blender versions

    triples = parse_key_data(key_data_str)

    action = ensure_action(obj)

    # Clear existing keyframes for the properties we're about to write
    paths_to_clear = [strength_path]
    if hasattr(field, "flow"):
        paths_to_clear.append(flow_path)
    remove_fcurves(action, paths_to_clear)

    # Write new keys
    for frame, strength, flow in triples:
        field.strength = strength
        obj.keyframe_insert(data_path=strength_path, frame=frame)

        if hasattr(field, "flow"):
            field.flow = flow
            obj.keyframe_insert(data_path=flow_path, frame=frame)

        print(f"{frame} {strength} {flow}")


if __name__ == "__main__":
    main(KEY_DATA)
