import bpy
import math
from mathutils import Quaternion, Vector

# --------------------------------
# USER PARAMETERS
# --------------------------------
DEG_PER_FRAME = -12
EXTRA_FRAMES  = 40

WORLD_Z = Vector((0.0, 0.0, 1.0))

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

# --------------------------------
# CORE LOGIC
# --------------------------------
def process_object(obj):
    scene = bpy.context.scene

    base_frame = 1
    base_world_q = eval_world_quat(scene, obj, base_frame)

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

        # Overwrite / insert key
        if obj.rotation_mode in {"QUATERNION", "AXIS_ANGLE"}:
            old_mode = obj.rotation_mode
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = new_e
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)
            obj.rotation_mode = old_mode
        else:
            obj.rotation_euler = new_e
            obj.keyframe_insert(data_path="rotation_euler", frame=frame)

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

process_object(terrain)
process_object(cross)

print("\nDone.")
