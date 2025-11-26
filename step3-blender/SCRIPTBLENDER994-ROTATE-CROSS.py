import bpy
import math

# ===========================
# Configuration
# ===========================

# Degrees added per accumulated unit of vortex strength
SCALE_DEGREES = 71

# Hardcoded additive value (degrees) for the 10th keyframe
HARDCODED_TENTH_DEGREES = 104.0

# Zero-crossing search parameters
SAMPLE_STEP = 0.25
BISECTION_MAX_ITERS = 40
BISECTION_TOL = 1e-4
VALUE_TOL = 1e-6

MAX_NEW_KEYS = 10
CROSS_NAMES = ("cross1", "cross2")

# ===========================
# Helpers
# ===========================

def find_single_vortex_object():
    vortex_objs = [obj for obj in bpy.data.objects
                   if hasattr(obj, "field") and obj.field and obj.field.type == 'VORTEX']
    if len(vortex_objs) != 1:
        raise RuntimeError(f"Expected exactly 1 Vortex force field, found {len(vortex_objs)}.")
    return vortex_objs[0]

def get_strength_fcurve(vortex_obj):
    ad = vortex_obj.animation_data
    if not ad or not ad.action:
        raise RuntimeError("Vortex object has no animation data/action (no keyframes).")
    for fc in ad.action.fcurves:
        if fc.data_path == "field.strength":
            return fc
    raise RuntimeError("Could not find F-Curve for field.strength on the vortex object.")

def sorted_keyframes(fcurve):
    return sorted(fcurve.keyframe_points, key=lambda kp: kp.co.x)

def f_eval(fcurve, frame):
    return fcurve.evaluate(frame)

def first_zero_crossing_in_interval(fcurve, f0, f1):
    """Find first frame in [f0, f1] where the bezier-interpolated strength crosses 0."""
    if f1 <= f0:
        return None
    a = f0
    va = f_eval(fcurve, a)
    if abs(va) <= VALUE_TOL:
        return a
    t = a + SAMPLE_STEP
    while t <= f1 + 1e-9:
        b = min(t, f1)
        vb = f_eval(fcurve, b)
        if abs(vb) <= VALUE_TOL:
            return b
        if (va < 0 and vb > 0) or (va > 0 and vb < 0):
            left, right = a, b
            vl, vr = va, vb
            for _ in range(BISECTION_MAX_ITERS):
                mid = 0.5 * (left + right)
                vm = f_eval(fcurve, mid)
                if abs(vm) <= VALUE_TOL or (right - left) <= BISECTION_TOL:
                    return mid
                if (vl < 0 and vm > 0) or (vl > 0 and vm < 0):
                    right, vr = mid, vm
                else:
                    left, vl = mid, vm
            return 0.5 * (left + right)
        a, va = b, vb
        t += SAMPLE_STEP
    return None

def find_zero_strength_keyframe_frame(fcurve):
    for kp in fcurve.keyframe_points:
        if abs(kp.co.y) <= VALUE_TOL:
            return kp.co.x
    return None

def get_object_or_fail(name):
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Required object '{name}' not found.")
    return obj

# ===========================
# Cumulative vortex computation
# ===========================

def build_cumulative_vortex(fcurve, frame_start, frame_end):
    """Build cumulative sum C[n] = sum of strength from start to frame n."""
    C = {}
    running = 0.0
    for fr in range(frame_start, frame_end + 1):
        running += f_eval(fcurve, fr)
        C[fr] = running
    return C, frame_start

def cumulative_at(t, C, frame_start, fcurve):
    """Get cumulative sum at fractional frame t."""
    if t <= frame_start:
        return 0.0
    ti = int(math.floor(t))
    base = C.get(ti, 0.0)
    frac = t - ti
    if frac <= 1e-9:
        return base
    return base + frac * f_eval(fcurve, t)

# ===========================
# Main
# ===========================

def main():
    scene = bpy.context.scene
    frame_start = scene.frame_start
    frame_end   = scene.frame_end
    current_frame = scene.frame_current

    vortex = find_single_vortex_object()
    fcurve = get_strength_fcurve(vortex)
    kps = sorted_keyframes(fcurve)
    if len(kps) < 3:
        raise RuntimeError("Need at least 3 keyframes on field.strength.")

    cross1 = get_object_or_fail(CROSS_NAMES[0])
    cross2 = get_object_or_fail(CROSS_NAMES[1])

    # Base rotations (degrees)
    scene.frame_set(frame_start)
    base_z_cross1_deg = math.degrees(cross1.rotation_euler[2])
    base_z_cross2_deg = math.degrees(cross2.rotation_euler[2])

    # Cumulative vortex precomputation
    C, C_start = build_cumulative_vortex(fcurve, frame_start, frame_end)

    # Determine placement frames
    placement_frames = []
    last_segment_index = len(kps) - 3
    for i in range(1, last_segment_index + 1):
        if len(placement_frames) >= 9:
            break
        f0 = kps[i].co.x
        f1 = kps[i + 1].co.x
        zf = first_zero_crossing_in_interval(fcurve, f0, f1)
        if zf is not None:
            placement_frames.append(zf)

    # 10th placement: at zero-strength keyframe (if exists)
    zero_key_frame = find_zero_strength_keyframe_frame(fcurve)
    if zero_key_frame is not None:
        placement_frames.append(zero_key_frame)

    placement_frames = placement_frames[:MAX_NEW_KEYS]
    if not placement_frames:
        raise RuntimeError("No zero crossings found.")
    placement_frames.sort()

    # Insert keyframes
    for idx, f in enumerate(placement_frames):
        if idx == 9:
            # 10th keyframe uses hardcoded additive
            add_deg = HARDCODED_TENTH_DEGREES
        else:
            cum = cumulative_at(f, C, C_start, fcurve)
            add_deg = SCALE_DEGREES * cum

        z1_deg = base_z_cross1_deg + add_deg
        z2_deg = base_z_cross2_deg + add_deg

        cross1.rotation_euler[2] = math.radians(z1_deg)
        cross1.keyframe_insert(data_path="rotation_euler", index=2, frame=f)

        cross2.rotation_euler[2] = math.radians(z2_deg)
        cross2.keyframe_insert(data_path="rotation_euler", index=2, frame=f)

        label = " (hardcoded 10th)" if idx == 9 else ""
        print(f"[Keyframe {idx+1}] frame={f:.4f} | add={add_deg:.3f}° | "
              f"cross1.z={z1_deg:.3f}° | cross2.z={z2_deg:.3f}°{label}")

    print(f"Placed {len(placement_frames)} rotation keyframes (SCALE={SCALE_DEGREES}°/unit, 10th={HARDCODED_TENTH_DEGREES}°).")

    scene.frame_set(current_frame)

# Run
try:
    main()
except Exception as e:
    print("ERROR:", e)
