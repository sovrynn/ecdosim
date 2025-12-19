import bpy

VORTEX_NAME = "Vortex-dynamic"
TARGET_NAMES = ["cross", "terrain"]


def log(msg: str):
    print(f"[Cleanup] {msg}")


def get_obj(name: str):
    return bpy.data.objects.get(name)


def remove_object_by_name(name: str) -> bool:
    obj = get_obj(name)
    if not obj:
        log(f'Object "{name}" not found (nothing to delete).')
        return False

    log(f'Deleting object "{name}"...')
    # Unlink from all collections first (safe cleanup)
    for col in list(obj.users_collection):
        col.objects.unlink(obj)

    bpy.data.objects.remove(obj, do_unlink=True)
    log(f'Deleted "{name}".')
    return True


def clear_keyframes(obj: bpy.types.Object):
    # Clears object animation/action
    if obj.animation_data:
        log(f'Clearing animation data on "{obj.name}"...')
    obj.animation_data_clear()

    # Also clear material animation (optional but often desired)
    if obj.active_material and obj.active_material.animation_data:
        log(f'Clearing material animation data on "{obj.name}" (active material "{obj.active_material.name}")...')
        obj.active_material.animation_data_clear()


def zero_rotation(obj: bpy.types.Object):
    obj.rotation_mode = "XYZ"  # ensure Euler
    obj.rotation_euler = (0.0, 0.0, 0.0)
    log(f'Set rotation of "{obj.name}" to (0, 0, 0).')


def main():
    log("Starting cleanup...")

    # 1) Delete Vortex-dynamic (if present)
    remove_object_by_name(VORTEX_NAME)

    # 2) For cross + terrain: delete all keyframes and zero rotation
    for name in TARGET_NAMES:
        obj = get_obj(name)
        if not obj:
            log(f'Object "{name}" not found (skipping).')
            continue

        log(f'Processing "{name}"...')
        clear_keyframes(obj)
        zero_rotation(obj)
        log(f'Finished "{name}".')

    log("Done.")


if __name__ == "__main__":
    main()
