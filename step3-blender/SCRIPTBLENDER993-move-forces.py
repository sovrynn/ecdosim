# sync_force_xy_from_vortex.py
import bpy

# -------------------------
# PARAMS — adjust as needed
# -------------------------
PLAIN_FORCE_NAMES = [
    "inward-squared-force",
    "inward-squared-negative",
]
# If you know the vortex object's name, put it here. Otherwise leave as None to auto-detect a single vortex.
VORTEX_NAME = None

# If True, will apply to *all* plain 'FORCE' type fields in the scene (ignores PLAIN_FORCE_NAMES).
APPLY_TO_ALL_PLAIN_FORCES = False

# -------------------------
# Helpers
# -------------------------
def is_force_field_object(obj, field_type: str) -> bool:
    """Return True if obj has a force field of the given type (e.g., 'FORCE', 'VORTEX')."""
    try:
        return hasattr(obj, "field") and obj.field is not None and obj.field.type == field_type
    except Exception:
        return False

def find_vortex(vortex_name=None):
    """Find a single vortex force field object. If name is provided, match that one; else require exactly one in the scene."""
    if vortex_name:
        obj = bpy.data.objects.get(vortex_name)
        if obj is None or not is_force_field_object(obj, "VORTEX"):
            raise RuntimeError(f"Vortex named '{vortex_name}' not found or not a VORTEX field.")
        return obj

    vortices = [o for o in bpy.data.objects if is_force_field_object(o, "VORTEX")]
    if len(vortices) == 0:
        raise RuntimeError("No VORTEX force field found in the scene.")
    if len(vortices) > 1:
        names = ", ".join(o.name for o in vortices)
        raise RuntimeError(f"Multiple VORTEX force fields found ({names}). Specify VORTEX_NAME to disambiguate.")
    return vortices[0]

def find_plain_forces(names=None, apply_all=False):
    """Find plain 'FORCE' type force field objects based on names or all in scene."""
    if apply_all:
        return [o for o in bpy.data.objects if is_force_field_object(o, "FORCE")]
    if not names:
        return []
    name_set = set(names)
    matches = []
    for o in bpy.data.objects:
        if o.name in name_set and is_force_field_object(o, "FORCE"):
            matches.append(o)
    return matches

# -------------------------
# Main
# -------------------------
def main():
    vortex = find_vortex(VORTEX_NAME)
    vx, vy = vortex.location.x, vortex.location.y

    plain_forces = find_plain_forces(PLAIN_FORCE_NAMES, APPLY_TO_ALL_PLAIN_FORCES)

    if not plain_forces:
        target_info = "all plain forces in scene" if APPLY_TO_ALL_PLAIN_FORCES else f"named: {', '.join(PLAIN_FORCE_NAMES)}"
        print(f"[INFO] No plain 'FORCE' fields found ({target_info}). Nothing to update.")
        print(f"[INFO] Vortex: '{vortex.name}' at ({vortex.location.x:.3f}, {vortex.location.y:.3f}, {vortex.location.z:.3f})")
        return

    print("=== Force XY Sync from Vortex ===")
    print(f"VORTEX: '{vortex.name}' @ ({vortex.location.x:.6f}, {vortex.location.y:.6f}, {vortex.location.z:.6f})")

    for obj in plain_forces:
        old_loc = obj.location.copy()
        obj.location.x = vx
        obj.location.y = vy
        # Z is intentionally left as-is
        new_loc = obj.location
        print(f"UPDATED: '{obj.name}' | type=FORCE | "
              f"old=({old_loc.x:.6f}, {old_loc.y:.6f}, {old_loc.z:.6f}) -> "
              f"new=({new_loc.x:.6f}, {new_loc.y:.6f}, {new_loc.z:.6f})")

    print("=== Done ===")

if __name__ == "__main__":
    main()
