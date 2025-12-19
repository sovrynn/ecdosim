import bpy
import math
from mathutils import Quaternion, Vector

# --------------------------------
# USER PARAMETERS
# --------------------------------
DEG_PER_FRAME = -12
EXTRA_FRAMES  = 40

WORLD_Z = Vector((0.0, 0.0, 1.0))

WHITE_RGBA = (1.0, 1.0, 1.0, 1.0)

# --------------------------------
# HELPERS
# --------------------------------
def get_obj(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f'Object "{name}" not found.')
    return obj

def eval_world_quat(scene, obj, frame):
    scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    return obj.evaluated_get(deps).matrix_world.to_quaternion()

def quat_to_euler(obj, quat):
    mode = obj.rotation_mode
    if mode in {"QUATERNION", "AXIS_ANGLE"}:
        mode = "XYZ"
    return quat.to_euler(mode)

def deg_xyz(e):
    return (
        math.degrees(e.x),
        math.degrees(e.y),
        math.degrees(e.z),
    )

def material_basecolor_sockets(mat):
    """
    Returns a list of (socket, keyframe_data_path) for Principled BSDF Base Color.
    If no node setup, returns [].
    """
    if not mat or not mat.use_nodes or not mat.node_tree:
        return []

    sockets = []
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            sock = node.inputs.get("Base Color")
            if sock and hasattr(sock, "default_value"):
                # Keyframing the socket's default_value directly works
                sockets.append(sock)
    return sockets

def keyframe_cross_shading(obj, frame, color_rgba):
    """
    Set + keyframe shading color for all materials on obj.
    Prefers Principled BSDF Base Color; falls back to material.diffuse_color.
    """
    if obj.type != "MESH" or not obj.data.materials:
        return

    for mat in obj.data.materials:
        if not mat:
            continue

        socks = material_basecolor_sockets(mat)
        if socks:
            for sock in socks:
                sock.default_value = color_rgba
                sock.keyframe_insert(data_path="default_value", frame=frame)
        else:
            # Fallback: viewport diffuse color (works for non-node materials / simple cases)
            mat.diffuse_color = color_rgba
            mat.keyframe_insert(data_path="diffuse_color", frame=frame)

# --------------------------------
# CORE LOGIC
# --------------------------------
def process_object(obj, set_white_preroll=False):
    scene = bpy.context.scene

    base_frame = 1
    base_world_q = eval_world_quat(scene, obj, base_frame)

    # If this is the cross: keyframe its original shading at the first keyframe
    if set_white_preroll:
        # Capture original color(s) at base_frame and keyframe them there
        # (so it returns to original at frame 1).
        for mat in (obj.data.materials if obj.type == "MESH" and obj.data.materials else []):
            if not mat:
                continue
            socks = material_basecolor_sockets(mat)
            if socks:
                for sock in socks:
                    orig = tuple(sock.default_value)
                    sock.default_value = orig
                    sock.keyframe_insert(data_path="default_value", frame=base_frame)
            else:
                orig = tuple(mat.diffuse_color)
                mat.diffuse_color = orig
                mat.keyframe_insert(data_path="diffuse_color", frame=base_frame)

    print(f"\n=== Processing '{obj.name}' ===")
    print("Frame | Original(deg XYZ) | AddWorldZ(deg, +CW) | NewOverwritten(deg XYZ)")

    for i in range(1, EXTRA_FRAMES + 1):
        frame = base_frame - i
        add_deg = -i * DEG_PER_FRAME        # subtract going backwards
        add_rad = -math.radians(add_deg)    # negate for +CW convention

        rotz_q = Quaternion(WORLD_Z, add_rad)
        new_world_q = rotz_q @ base_world_q

        orig_e = quat_to_euler(obj, base_world_q)
        new_e  = quat_to_euler(obj, new_world_q)

        # Overwrite / insert rotation key
        if obj.rotation_mode in {"QUATERNION", "AXIS_ANGLE"}:
            old_mode = obj.rotation_mode
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = new_e
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)
            obj.rotation_mode = old_mode
        else:
            obj.rotation_euler = new_e
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)

        # If this is the cross: make ALL preroll-added keys white
        if set_white_preroll:
            keyframe_cross_shading(obj, frame, WHITE_RGBA)

        print(
            f"{frame:5d} | "
            f"{deg_xyz(orig_e)!s:>20} | "
            f"{add_deg:15.6f} | "
            f"{deg_xyz(new_e)!s:>22}"
        )

# --------------------------------
# MAIN
# --------------------------------
terrain = get_obj("terrain")
cross   = get_obj("cross")

process_object(terrain, set_white_preroll=False)
process_object(cross,   set_white_preroll=True)

print("\nDone.")
