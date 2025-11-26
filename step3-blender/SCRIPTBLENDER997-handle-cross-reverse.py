import bpy
import math

# ----------------------------
# Parameters (tweak as needed)
# ----------------------------
SCALE = 79        # running-sum scale factor
SCALE = 67.23
TOTAL_KEYS = 10      # number of zero-crossing frames to add (for each cross object)
START_FRAME = 2      # start frame for accumulation and zero-crossing checks

# ----------------------------
# Helpers
# ----------------------------
def find_vortex_force():
    """Return the single object that has a VORTEX force field, or None."""
    for obj in bpy.data.objects:
        fld = getattr(obj, "field", None)
        if fld and fld.type == 'VORTEX':
            return obj
    return None

def eval_strength_at_frame(obj, frame):
    """Evaluate the vortex strength at a given frame by setting the scene frame."""
    bpy.context.scene.frame_set(frame)
    return obj.field.strength

def get_z_deg_at_frame(obj, frame):
    """Rotation Z in DEGREES at a given frame (reads current evaluated value)."""
    bpy.context.scene.frame_set(frame)
    return math.degrees(obj.rotation_euler[2])

def set_key_z_deg(obj, frame, z_deg):
    """Set rotation Z in degrees and insert a keyframe for that channel only."""
    obj.rotation_mode = obj.rotation_mode or 'XYZ'
    obj.rotation_euler[2] = math.radians(z_deg)
    obj.keyframe_insert(data_path="rotation_euler", index=2, frame=frame)

# ----------------------------
# Locate scene objects
# ----------------------------
scene = bpy.context.scene
if scene is None:
    raise RuntimeError("No active scene found.")

vortex = find_vortex_force()
if vortex is None:
    raise RuntimeError("Could not find a VORTEX force field object in the scene.")

cross1 = bpy.data.objects.get("cross1")
cross2 = bpy.data.objects.get("cross2")
if cross1 is None or cross2 is None:
    missing = [name for name, obj in [("cross1", cross1), ("cross2", cross2)] if obj is None]
    raise RuntimeError(f"Missing object(s): {', '.join(missing)}")

# ----------------------------
# Set initial baseline keys @ frame 1 (as requested)
# ----------------------------
set_key_z_deg(cross1, 1, 0.0)
set_key_z_deg(cross2, 1, 90.0)

# Read baselines after inserting the initial keys
base_z_deg_cross1 = get_z_deg_at_frame(cross1, 1)
base_z_deg_cross2 = get_z_deg_at_frame(cross2, 1)

# ----------------------------
# Accumulate & detect zero crossings
# ----------------------------
frame_end = scene.frame_end
if START_FRAME < 2:
    START_FRAME = 2

running_sum = 0.0
last_val = eval_strength_at_frame(vortex, START_FRAME - 1)
keys_added = 0

for f in range(START_FRAME, frame_end + 1):
    val = eval_strength_at_frame(vortex, f)
    running_sum += (val * SCALE)

    crossed = False
    if val == 0.0:
        crossed = True
    elif (last_val < 0.0 and val > 0.0) or (last_val > 0.0 and val < 0.0):
        crossed = True

    if crossed:
        # Subtractive instead of additive
        sub_deg = -running_sum

        # cross1
        new_z_deg_1 = base_z_deg_cross1 + sub_deg
        set_key_z_deg(cross1, f, new_z_deg_1)
        print(f"[cross1] frame={f}  z0(deg)={base_z_deg_cross1:.6f}  -sum(deg)={-sub_deg:.6f}  => z_new(deg)={new_z_deg_1:.6f}")

        # cross2
        new_z_deg_2 = base_z_deg_cross2 + sub_deg
        set_key_z_deg(cross2, f, new_z_deg_2)
        print(f"[cross2] frame={f}  z0(deg)={base_z_deg_cross2:.6f}  -sum(deg)={-sub_deg:.6f}  => z_new(deg)={new_z_deg_2:.6f}")

        keys_added += 1
        if keys_added >= TOTAL_KEYS:
            break

    last_val = val

# Optional: restore current frame
# scene.frame_set(scene.frame_current)
