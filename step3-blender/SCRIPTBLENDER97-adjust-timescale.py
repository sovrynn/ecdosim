import bpy

# --- Boilerplate from prompt (kept as-is) ---
TARGETS = ("inward-squared-force", "inward-squared-negative")
TARGETS = ("in-constant", "in-constant-negative", "in-large", "in-large-negative", "in-small", "in-small-negative")
TARGETS = ("constant", "constant-negative", "large", "large-negative", "small", "small-negative", "huge", "huge-negative")
FACTOR = 1.34
DATA_PATH = "field.strength"
# -------------------------------------------

SCALE = FACTOR  # Interpret FACTOR as the time-scale multiplier for keyframe spacing

FORCE_TYPES_TO_INCLUDE = {"FORCE", "VORTEX"}  # 'FORCE' = basic attractive/repulsive, plus all VORTEX fields
FLOW_DATA_PATH = "field.flow"                 # Flow anim path for VORTEX force fields

EPS = 1e-6


def iter_strength_fcurves(obj, data_path):
    """Yield all F-Curves on the given data_path (usually 'field.strength')."""
    ad = getattr(obj, "animation_data", None)
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path == data_path:
            yield fc


def iter_property_fcurves(obj, data_path):
    """Generic iterator for F-Curves on any given data_path."""
    ad = getattr(obj, "animation_data", None)
    if not ad or not ad.action:
        return
    for fc in ad.action.fcurves:
        if fc.data_path == data_path:
            yield fc


def retime_keyframes_by_scale(fc, scale):
    """
    Retime keyframes so that times are scaled *around frame 1*:

        new_frame = 1 + (old_frame - 1) * scale

    Special rules:
    - Keys at frame 1 stay at 1 (anchor).
    - Keys at frame 0 NEVER move.
    - Handles' X positions are shifted by the same delta as their key.

    This ensures the 'first keyframe' (earliest non-zero key) moves by its
    distance * scale from frame 1, while frame 0 remains fixed.
    """
    kfs = list(fc.keyframe_points)
    if len(kfs) < 1:
        return []

    # Build a fast test for whether a frame equals 0 or 1
    def is_frame(f, target):
        return abs(f - target) < EPS

    # Apply transform
    for k in kfs:
        old_f = k.co[0]

        # Never move exact frame 0
        if is_frame(old_f, 0.0):
            continue

        # Keep exact frame 1 as anchor
        if is_frame(old_f, 1.0):
            continue

        new_f = 1.0 + (old_f - 1.0) * scale
        dx = new_f - old_f

        # Update key and handles by same delta on X
        k.co[0] = new_f
        k.handle_left[0] += dx
        k.handle_right[0] += dx

    fc.update()
    return [(k.co[0], k.co[1]) for k in sorted(fc.keyframe_points, key=lambda p: (p.co[0], p.co[1]))]


def collect_targets():
    """
    Collect:
      1) Named targets listed in TARGETS *that are basic FORCE fields* (attractive/repulsive), and
      2) All VORTEX force fields in the scene (regardless of name).
    Return a unique, ordered list of objects.
    """
    out = []
    seen = set()

    # 1) Named targets limited to FORCE type (basic attract/repel)
    for name in TARGETS:
        obj = bpy.data.objects.get(name)
        if obj and getattr(obj, "field", None) and obj.field.type == "FORCE":
            if obj.name not in seen:
                out.append(obj)
                seen.add(obj.name)

    # 2) All VORTEX fields (any name)
    for obj in bpy.data.objects:
        fld = getattr(obj, "field", None)
        if fld and fld.type == "VORTEX":
            if obj.name not in seen:
                out.append(obj)
                seen.add(obj.name)

    return out


def retime_property_on_obj(obj, data_path, scale, label):
    """
    Helper: retime all F-Curves on `data_path` for `obj`.
    Returns (any_changed: bool).
    """
    fcurves = list(iter_property_fcurves(obj, data_path))
    if not fcurves:
        print(f'[{obj.name}] has no keyframes on "{data_path}"; skipping.')
        return False

    any_changed = False
    for fc in fcurves:
        before_frames = sorted([k.co[0] for k in fc.keyframe_points])
        after = retime_keyframes_by_scale(fc, scale)
        after_frames = [f for (f, _v) in after]
        if len(before_frames) != len(after_frames):
            any_changed = True
        else:
            if any(abs(a - b) > EPS for a, b in zip(sorted(before_frames), sorted(after_frames))):
                any_changed = True

    # Log final keyframes (frame + value) after retime
    for fc in iter_property_fcurves(obj, data_path):
        keys = sorted(fc.keyframe_points, key=lambda k: (k.co[0], k.co[1]))
        for k in keys:
            print(f'  [{obj.name}] frame {k.co[0]:g}: {label} {k.co[1]:.6g}')

    if not any_changed:
        print(f'[{obj.name}] Nothing to retime on "{data_path}" (no frame changes after applying rules).')

    return any_changed


def retime_strength_and_flow_keyframes(obj, scale):
    """
    Retime strength keyframes on the given object and, if it's a VORTEX field,
    also retime 'flow' so it moves together with the strength timing.
    """
    if obj is None:
        print("Object is None.")
        return

    fld = getattr(obj, "field", None)
    if not fld:
        print(f'[{obj.name}] has no force field settings; skipping.')
        return

    if fld.type not in FORCE_TYPES_TO_INCLUDE:
        print(f'[{obj.name}] force type "{fld.type}" not in {FORCE_TYPES_TO_INCLUDE}; skipping.')
        return

    ad = getattr(obj, "animation_data", None)
    if not ad or not ad.action:
        print(f'[{obj.name}] has no animation data/action; skipping.')
        return

    # --- Strength ---
    print(f'[{obj.name}] Retiming keyframes on "{DATA_PATH}" with SCALE={scale:g} (type={fld.type})')
    strength_changed = retime_property_on_obj(obj, DATA_PATH, scale, label="strength")

    # --- Flow (only for VORTEX) ---
    if fld.type == "VORTEX":
        print(f'[{obj.name}] Retiming VORTEX "flow" to match timing (SCALE={scale:g})')
        _flow_changed = retime_property_on_obj(obj, FLOW_DATA_PATH, scale, label="flow")


def main():
    targets = collect_targets()
    if not targets:
        print("No matching FORCE/VORTEX force fields found based on TARGETS and VORTEX search.")
        return

    for obj in targets:
        retime_strength_and_flow_keyframes(obj, SCALE)


if __name__ == "__main__":
    main()
