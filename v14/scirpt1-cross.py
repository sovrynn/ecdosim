import bpy

# -----------------------
# Parameters (edit these)
# -----------------------
COLOR_POS  = (0.0, 0.0, 1.0, 1.0)  # + strength  -> Blue
COLOR_NEG  = (1.0, 0.0, 0.0, 1.0)  # - strength  -> Red
COLOR_ZERO = (1.0, 1.0, 1.0, 1.0)  # 0 strength  -> White

# Width rule you described:
# - When strength == 0  -> scale XY = 1 (default)
# - Otherwise           -> scale XY = 1 + abs(strength)
BASE_SCALE_XY = 1.0     # default width scale when strength == 0 (must be >= 1.0)
KEEP_Z_SCALE = True     # keep cylinder Z scale unchanged

MATERIAL_NAME = "Cross_AutoMaterial"
PRINCIPLED_NODE_NAME = "Principled BSDF"
PRINCIPLED_COLOR_SOCKET = "Base Color"
CROSS_NAME = "cross"
VORTEX_NAME = "Vortex-dynamic"
# -----------------------


def get_obj(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f'Object "{name}" not found.')
    return obj


def clear_all_keyframes(obj: bpy.types.Object):
    obj.animation_data_clear()
    if obj.active_material and obj.active_material.animation_data:
        obj.active_material.animation_data_clear()


def ensure_material_with_principled(obj: bpy.types.Object) -> bpy.types.Material:
    mat = obj.active_material
    if mat is None:
        mat = bpy.data.materials.get(MATERIAL_NAME) or bpy.data.materials.new(MATERIAL_NAME)
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        obj.active_material = mat

    mat.use_nodes = True
    nt = mat.node_tree

    principled = nt.nodes.get(PRINCIPLED_NODE_NAME)
    if principled is None:
        principled = nt.nodes.new(type="ShaderNodeBsdfPrincipled")
        principled.name = PRINCIPLED_NODE_NAME
        principled.label = PRINCIPLED_NODE_NAME

        out = nt.nodes.get("Material Output") or nt.nodes.new(type="ShaderNodeOutputMaterial")
        out.name = "Material Output"
        if principled.outputs.get("BSDF") and out.inputs.get("Surface"):
            nt.links.new(principled.outputs["BSDF"], out.inputs["Surface"])

    return mat


def set_material_color_keyframe(mat: bpy.types.Material, rgba, frame: int):
    nt = mat.node_tree
    principled = nt.nodes.get(PRINCIPLED_NODE_NAME)
    sock = principled.inputs.get(PRINCIPLED_COLOR_SOCKET)
    sock.default_value = rgba
    sock.keyframe_insert(data_path="default_value", frame=frame)


def collect_keyframes(obj: bpy.types.Object) -> list[int]:
    frames = set()
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    for fc in ad.action.fcurves:
        for kp in fc.keyframe_points:
            frames.add(int(round(kp.co.x)))
    return sorted(frames)


def main():
    scene = bpy.context.scene

    vortex = get_obj(VORTEX_NAME)
    cross = get_obj(CROSS_NAME)

    if vortex.field is None:
        raise RuntimeError('"Vortex" does not have a force field (vortex.field is None).')

    # Remove all keyframes for cross (object + material)
    clear_all_keyframes(cross)

    # Ensure material to animate color
    mat = ensure_material_with_principled(cross)

    base_xy = max(1.0, float(BASE_SCALE_XY))
    base_z = float(cross.scale.z)

    frames = collect_keyframes(vortex)
    if not frames:
        print('No keyframes found on "Vortex". Nothing to do.')
        return

    for f in frames:
        scene.frame_set(f)

        strength = float(vortex.field.strength)

        # Color logic
        if strength > 0.0:
            col = COLOR_POS
        elif strength < 0.0:
            col = COLOR_NEG
        else:
            col = COLOR_ZERO

        # ---- WIDTH SCALE (X/Y) ----
        # Always at least 1.0. Add abs(strength) to the base width.
        # strength=0 -> 1.0
        # strength=+2 -> 3.0
        # strength=-2 -> 3.0
        xy = max(1.0, base_xy + abs(strength))
        cross.scale.x = xy
        cross.scale.y = xy
        if KEEP_Z_SCALE:
            cross.scale.z = base_z

        cross.keyframe_insert(data_path="scale", frame=f)

        # ---- ROTATION: paste vortex rotation over cross rotation ----
        cross.rotation_euler = vortex.rotation_euler
        cross.keyframe_insert(data_path="rotation_euler", frame=f)

        # ---- MATERIAL COLOR ----
        set_material_color_keyframe(mat, col, f)

        # Print what we wrote
        print(
            f"[frame {f}] strength={strength:.6g} "
            f"scaleXY=({cross.scale.x:.4f}, {cross.scale.y:.4f}) "
            f"rot=({cross.rotation_euler.x:.4f}, {cross.rotation_euler.y:.4f}, {cross.rotation_euler.z:.4f}) "
            f"color={tuple(round(c, 4) for c in col)}"
        )

    print("Done.")


if __name__ == "__main__":
    main()
