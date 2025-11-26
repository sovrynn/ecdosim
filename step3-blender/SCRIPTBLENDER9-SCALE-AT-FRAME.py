import bpy
from math import isclose

# ===== Parameters =====
FRAME = 1          # <-- Set the frame you care about
SCALE = 0.5        # <-- Multiplier to apply when FRAME is a keyed frame

# ===== Helpers =====

def find_object_by_name_and_force_type(name, force_type):
    """Return object by exact name if it exists and is the given force type, else None."""
    obj = bpy.data.objects.get(name)
    if obj and getattr(obj, "field", None) and obj.field.type == force_type:
        return obj
    return None

def find_first_force_by_type(force_type):
    """Return the first object in the scene with a force field of the given type, else None."""
    for obj in bpy.data.objects:
        if getattr(obj, "field", None) and obj.field.type == force_type:
            return obj
    return None

def fcurve_has_key_at_frame(obj, data_path, frame):
    """
    Check if `obj` has an fcurve for `data_path` with a keyframe exactly at `frame`.
    Blender stores keyframe x as float frame index.
    """
    ad = obj.animation_data
    if not ad or not ad.action:
        return False
    # Match fcurves whose data_path equals the given path (no array_index for scalars)
    for fc in ad.action.fcurves:
        if fc.data_path == data_path:
            for kp in fc.keyframe_points:
                # kp.co.x is the frame number (float)
                if isclose(kp.co.x, float(frame), rel_tol=0.0, abs_tol=1e-4):
                    return True
    return False

def maybe_scale_property(obj, label, data_path, getter, setter, frame, scale):
    """
    If `data_path` has a keyframe at `frame`, multiply its current value by `scale`.
    Print before/after. Return True if modified.
    """
    if fcurve_has_key_at_frame(obj, data_path, frame):
        old_val = getter()
        new_val = old_val * scale
        setter(new_val)
        print(f"[{label}] {data_path}: {old_val:.6g} -> {new_val:.6g} (frame {frame}) on object '{obj.name}'")
        return True
    else:
        # Optional: Uncomment to see when a property was skipped due to no key at FRAME
        # print(f"[SKIP] No key at frame {frame} for {data_path} on '{obj.name}'")
        return False

def process_plain_force(obj, frame, scale):
    """Process a plain force (type FORCE): scale strength if keyed at FRAME."""
    if not obj or not getattr(obj, "field", None) or obj.field.type != 'FORCE':
        return
    # strength lives at object.field.strength (data_path on object: 'field.strength')
    maybe_scale_property(
        obj=obj,
        label="Plain Force",
        data_path="field.strength",
        getter=lambda: obj.field.strength,
        setter=lambda v: setattr(obj.field, "strength", v),
        frame=frame,
        scale=scale
    )

def process_vortex_force(obj, frame, scale):
    """Process a vortex force (type VORTEX): scale strength and flow if keyed at FRAME."""
    if not obj or not getattr(obj, "field", None) or obj.field.type != 'VORTEX':
        return
    # strength
    strength_changed = maybe_scale_property(
        obj=obj,
        label="Vortex",
        data_path="field.strength",
        getter=lambda: obj.field.strength,
        setter=lambda v: setattr(obj.field, "strength", v),
        frame=frame,
        scale=scale
    )
    # flow (only VORTEX uses it meaningfully)
    if hasattr(obj.field, "flow"):
        flow_changed = maybe_scale_property(
            obj=obj,
            label="Vortex",
            data_path="field.flow",
            getter=lambda: obj.field.flow,
            setter=lambda v: setattr(obj.field, "flow", v),
            frame=frame,
            scale=scale
        )
    else:
        flow_changed = False

    if not (strength_changed or flow_changed):
        # Optional: Uncomment for visibility when nothing changed
        # print(f"[SKIP] No keyed strength/flow at frame {frame} for vortex '{obj.name}'")
        pass

# ===== Main =====

def main(frame=FRAME, scale=SCALE):
    # Find the two named plain forces
    pf1 = find_object_by_name_and_force_type("inward-squared-force", 'FORCE')
    pf2 = find_object_by_name_and_force_type("inward-squared-negative", 'FORCE')

    # Find any vortex force (first found)
    vortex = find_first_force_by_type('VORTEX')

    if not pf1:
        print("WARNING: Plain force 'inward-squared-force' (type FORCE) not found or wrong type.")
    if not pf2:
        print("WARNING: Plain force 'inward-squared-negative' (type FORCE) not found or wrong type.")
    if not vortex:
        print("WARNING: No vortex (type VORTEX) force found in the scene.")

    # Apply scaling if the given frame is a keyframe for the relevant properties
    if pf1:
        process_plain_force(pf1, frame, scale)
    if pf2:
        process_plain_force(pf2, frame, scale)
    if vortex:
        process_vortex_force(vortex, frame, scale)

# Run immediately when the script is executed in Blender's Text Editor
if __name__ == "__main__":
    main()
