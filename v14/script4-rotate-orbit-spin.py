import bpy
import math
from mathutils import Quaternion, Vector

# -----------------------------
# USER PARAMETERS
# -----------------------------
DEG_PER_FRAME = -12     # degrees per frame increment (1x, 2x, 3x, ...)
EXTRA_FRAMES  = 40       # number of extra frames after last TERRAIN keyframe

# -----------------------------
# HELPERS
# -----------------------------
WORLD_Z = Vector((0.0, 0.0, 1.0))

def get_obj(name: str) -> bpy.types.Object:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f'Object "{name}" not found in the scene.')
    return obj

def get_rotation_keyframes(obj: bpy.types.Object):
    """
    Returns (frames_sorted, first_frame, last_frame) for rotation_euler keyframes.
    If no rotation keyframes exist, raises.
    """
    ad = obj.animation_data
    if not ad or not ad.action:
        raise RuntimeError(f'Object "{obj.name}" has no animation action.')

    frames = set()
    for fc in ad.action.fcurves:
        if fc.data_path == "rotation_euler" and fc.array_index in (0, 1, 2):
            for kp in fc.keyframe_points:
                frames.add(int(round(kp.co.x)))

    if not frames:
        raise RuntimeError(f'Object "{obj.name}" has no rotation_euler keyframes.')

    frames_sorted = sorted(frames)
    return frames_sorted, frames_sorted[0], frames_sorted[-1]

def eval_world_quat_at_frame(scene: bpy.types.Scene, obj: bpy.types.Object, frame: int) -> Quaternion:
    """
    Evaluates the object's WORLD rotation at a given frame.
    """
    scene.frame_set(frame)
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(deps)
    return obj_eval.matrix_world.to_quaternion()

def quat_to_euler_like_obj(obj: bpy.types.Object, q: Quaternion):
    """
    Converts quaternion -> Euler in the object's rotation_mode.
    If object isn't in an Euler mode, temporarily treat as XYZ.
    """
    mode = obj.rotation_mode
    if mode in {"QUATERNION", "AXIS_ANGLE"}:
        mode = "XYZ"
    return q.to_euler(mode)

def rad_to_deg3(e):
    return (math.degrees(e.x), math.degrees(e.y), math.degrees(e.z))

def apply_world_z_increment_and_key(obj: bpy.types.Object,
                                    first_frame: int,
                                    last_terrain_frame: int,
                                    extra_frames: int,
                                    deg_per_frame: float):
    scene = bpy.context.scene

    # Cache last-frame world rotation for constant hold beyond last_terrain_frame
    last_world_q = eval_world_quat_at_frame(scene, obj, last_terrain_frame)

    start = first_frame
    end   = last_terrain_frame + extra_frames

    print(f"\n=== Processing '{obj.name}' from frame {start} (untouched) to {end} ===")
    print("Frame | Original(deg XYZ) | AddWorldZ(deg, +CW) | NewOverwritten(deg XYZ)")

    for f in range(start, end + 1):
        if f == start:
            # Leave first frame untouched, but still print original for clarity
            orig_q = eval_world_quat_at_frame(scene, obj, f)
            orig_e = quat_to_euler_like_obj(obj, orig_q)
            print(f"{f:5d} | {rad_to_deg3(orig_e)!s:>20} | {0.0:>15.6f} | {rad_to_deg3(orig_e)!s:>22}")
            continue

        # Increasing amount: next keyframe = 1*DEG_PER_FRAME, then 2*..., etc.
        step_count = (f - start)  # 1,2,3,...
        add_deg = step_count * deg_per_frame

        # Positive should be clockwise -> negate for Blender's right-hand rule
        add_rad = -math.radians(add_deg)

        # Evaluate "original" at this frame (but after last terrain frame, hold constant)
        if f <= last_terrain_frame:
            orig_q = eval_world_quat_at_frame(scene, obj, f)
        else:
            orig_q = last_world_q.copy()

        # Apply rotation about WORLD Z "on top of" existing: pre-multiply
        rotz_q = Quaternion(WORLD_Z, add_rad)
        new_q = rotz_q @ orig_q

        orig_e = quat_to_euler_like_obj(obj, orig_q)
        new_e  = quat_to_euler_like_obj(obj, new_q)

        # Overwrite keys: set euler then insert keyframe
        # (Ensures a key is created for EXTRA_FRAMES too.)
        if obj.rotation_mode in {"QUATERNION", "AXIS_ANGLE"}:
            # Force Euler overwrite path; keep the object's mode unchanged
            old_mode = obj.rotation_mode
            obj.rotation_mode = "XYZ"
            obj.rotation_euler = new_e
            obj.keyframe_insert(data_path="rotation_euler", frame=f)
            obj.rotation_mode = old_mode
        else:
            obj.rotation_euler = new_e
            obj.keyframe_insert(data_path="rotation_euler", frame=f)

        print(f"{f:5d} | {rad_to_deg3(orig_e)!s:>20} | {add_deg:15.6f} | {rad_to_deg3(new_e)!s:>22}")

# -----------------------------
# MAIN
# -----------------------------
terrain = get_obj("terrain")
cross   = get_obj("cross")

# Use TERRAIN's first/last keyframes as the master timeline
terrain_frames, first_frame, last_terrain_frame = get_rotation_keyframes(terrain)

# Apply to both terrain and cross using terrain's last frame + EXTRA_FRAMES
apply_world_z_increment_and_key(terrain, first_frame, last_terrain_frame, EXTRA_FRAMES, DEG_PER_FRAME)
apply_world_z_increment_and_key(cross,   first_frame, last_terrain_frame, EXTRA_FRAMES, DEG_PER_FRAME)

print("\nDone.")
