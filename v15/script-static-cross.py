import bpy

CROSS_OBJ_NAME = "cross"
VORTEX_OBJ_NAME = "Vortex"  # <-- change this if your vortex object has a different name

# -----------------------------
# Helpers
# -----------------------------
def get_obj(name: str):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f'Object "{name}" not found.')
    return obj

def clear_object_animation(obj: bpy.types.Object):
    if obj.animation_data and obj.animation_data.action:
        obj.animation_data.action.fcurves.clear()
    # Also clear NLA tracks if any (optional but usually desired when "delete all keyframes")
    if obj.animation_data and obj.animation_data.nla_tracks:
        for tr in list(obj.animation_data.nla_tracks):
            obj.animation_data.nla_tracks.remove(tr)

def ensure_principled_material(obj: bpy.types.Object) -> bpy.types.Material:
    if not obj.data or not hasattr(obj.data, "materials"):
        raise RuntimeError(f'Object "{obj.name}" does not support materials.')

    # Get or create a material slot
    if obj.data.materials and obj.data.materials[0]:
        mat = obj.data.materials[0]
    else:
        mat = bpy.data.materials.new(name=f"{obj.name}_Mat")
        obj.data.materials.append(mat)

    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links

    # Find or create Principled + Output
    principled = None
    output = None
    for n in nodes:
        if n.type == "BSDF_PRINCIPLED":
            principled = n
        elif n.type == "OUTPUT_MATERIAL":
            output = n

    if principled is None:
        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.location = (0, 0)

    if output is None:
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (300, 0)

    # Ensure they are linked
    if not any(l.to_node == output and l.from_node == principled for l in links):
        # Remove existing links into output surface to avoid multiple
        for l in list(output.inputs["Surface"].links):
            links.remove(l)
        links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    return mat

def key_material_base_color(mat: bpy.types.Material, frame: int, rgba):
    # Keyframe Principled Base Color
    principled = None
    for n in mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            principled = n
            break
    if principled is None:
        raise RuntimeError(f'Material "{mat.name}" has no Principled BSDF node.')

    principled.inputs["Base Color"].default_value = rgba
    principled.inputs["Base Color"].keyframe_insert(data_path="default_value", frame=frame)

def collect_keyed_frames_for_strength(vortex_obj: bpy.types.Object):
    """
    Collect frames where the vortex force-field "strength" is keyed.
    Tries common properties: field.strength, field.flow.
    Returns (data_path, sorted_frames) where data_path is the property path to evaluate.
    """
    if vortex_obj.field is None:
        raise RuntimeError(f'Object "{vortex_obj.name}" has no force field (obj.field is None).')

    ad = vortex_obj.animation_data
    if not (ad and ad.action):
        raise RuntimeError(f'Object "{vortex_obj.name}" has no animation action to read keyframes from.')

    # Candidate properties used across Blender versions / setups
    candidates = [
        'field.strength',
        'field.flow',
    ]

    found = {}
    for fcu in ad.action.fcurves:
        if fcu.data_path in candidates:
            frames = set()
            for kp in fcu.keyframe_points:
                frames.add(int(round(kp.co.x)))
            if frames:
                found[fcu.data_path] = sorted(frames)

    # Prefer field.strength if present, else any other
    if 'field.strength' in found:
        return 'field.strength', found['field.strength']

    if found:
        # return first found entry
        data_path = next(iter(found.keys()))
        return data_path, found[data_path]

    raise RuntimeError(
        f'No keyframes found on {candidates} for "{vortex_obj.name}". '
        f'Keyframe the force strength (Field > Strength) and try again.'
    )

def eval_vortex_strength_at_frame(vortex_obj: bpy.types.Object, data_path: str, frame: int) -> float:
    scene = bpy.context.scene
    old_frame = scene.frame_current
    scene.frame_set(frame)

    # Evaluate using the data_path we discovered
    # data_path is like 'field.strength' or 'field.flow'
    val = None
    if data_path == 'field.strength':
        val = float(vortex_obj.field.strength)
    elif data_path == 'field.flow':
        val = float(vortex_obj.field.flow)
    else:
        # fallback: try resolving dynamically (rarely needed)
        # minimal safe approach:
        raise RuntimeError(f"Unsupported strength data_path: {data_path}")

    scene.frame_set(old_frame)
    return val

# -----------------------------
# Main
# -----------------------------
try:
    scene = bpy.context.scene

    cross = get_obj(CROSS_OBJ_NAME)
    vortex = get_obj(VORTEX_OBJ_NAME)

    # Delete all keyframes on cross
    clear_object_animation(cross)

    # Set cross rotation to 0,0,0 initially
    cross.rotation_euler = (0.0, 0.0, 0.0)

    # Ensure material we will key
    mat = ensure_principled_material(cross)

    # Remember base scale
    base_sx, base_sy, base_sz = cross.scale.x, cross.scale.y, cross.scale.z

    # Collect frames where vortex strength is keyed
    strength_path, keyed_frames = collect_keyed_frames_for_strength(vortex)

    print(f'[INFO] Found {len(keyed_frames)} keyed frames on "{vortex.name}" ({strength_path}): {keyed_frames}')

    # Match cross rotation to vortex rotation (vortex doesn't move)
    cross.rotation_euler = vortex.rotation_euler

    # Optionally key that rotation once at frame start (not required, but harmless)
    # If you truly don't want a rotation keyframe, comment these two lines.
    # start_frame = keyed_frames[0] if keyed_frames else scene.frame_start
    # cross.keyframe_insert(data_path="rotation_euler", frame=start_frame)

    # For each strength keyframe, drive cross scale XY + material color
    for fr in keyed_frames:
        strength = eval_vortex_strength_at_frame(vortex, strength_path, fr)

        # Color logic
        if strength == 0.0:
            color = (1.0, 1.0, 1.0, 1.0)  # white
        elif strength < 0.0:
            color = (1.0, 0.0, 0.0, 1.0)  # red
        else:
            color = (0.0, 0.0, 1.0, 1.0)  # blue

        # Scale logic: scale_xy = base_xy * (1 + 10*strength)
        factor = 1.0 + 10.0 * strength
        cross.scale.x = base_sx * factor
        cross.scale.y = base_sy * factor
        cross.scale.z = base_sz  # unchanged

        # Set frame, then keyframe scale and material color
        scene.frame_set(fr)
        cross.keyframe_insert(data_path="scale", frame=fr)
        key_material_base_color(mat, fr, color)

        print(
            f'[KEYFRAME] frame={fr} strength={strength:.6f} '
            f'factor={factor:.6f} '
            f'scale=({cross.scale.x:.6f}, {cross.scale.y:.6f}, {cross.scale.z:.6f}) '
            f'color={color}'
        )

    print('[DONE] Completed keyframing "cross" from Vortex force-field strength.')

except Exception as e:
    print(f'[ERROR] {e}')
