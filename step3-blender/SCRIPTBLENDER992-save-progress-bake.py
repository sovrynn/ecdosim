import bpy
import os
import re

CHUNK = 5  # bake every 5 frames before saving metadata


def get_domain_named_DOMAIN():
    """Find a fluid domain object literally named 'DOMAIN'."""
    obj = bpy.data.objects.get("DOMAIN")
    if not obj:
        raise RuntimeError("❌ No object named 'DOMAIN' found in the scene.")
    for mod in obj.modifiers:
        if mod.type == 'FLUID' and getattr(mod, "fluid_type", "") == 'DOMAIN':
            return obj
    raise RuntimeError("❌ 'DOMAIN' exists but is not a Fluid DOMAIN object.")


def detect_last_baked_frame(cache_dir: str):
    """Scan Blender's cache directory and return the highest baked frame number."""
    if not cache_dir or not os.path.isdir(cache_dir):
        return None

    highest = None
    num_re = re.compile(r"(\d{1,6})(?=\D|$)")
    for root, _, files in os.walk(cache_dir):
        for f in files:
            if f.endswith((".uni", ".vdb", ".bobj.gz")):
                m = num_re.search(f)
                if m:
                    try:
                        n = int(m.group(1))
                        highest = n if highest is None or n > highest else highest
                    except ValueError:
                        continue
    return highest


def bake_all_in_chunks_all_cache():
    domain_obj = get_domain_named_DOMAIN()
    domain_mod = domain_obj.modifiers["Fluid"]
    ds = domain_mod.domain_settings

    # Force cache type to 'ALL' (continuous bake)
    ds.cache_type = 'ALL'

    cache_dir = bpy.path.abspath(ds.cache_directory)
    if not cache_dir:
        raise RuntimeError("⚠️ Domain cache directory not set! Please set it in the Physics > Fluid > Cache panel.")
    os.makedirs(cache_dir, exist_ok=True)

    scene = bpy.context.scene
    orig_start = scene.frame_start
    orig_end = scene.frame_end

    # Determine resume point from cache metadata
    last_baked = detect_last_baked_frame(cache_dir)
    start_frame = (last_baked + 1) if last_baked is not None else orig_start

    if start_frame > orig_end:
        print(f"✅ Nothing to bake. Cache appears complete up to frame {orig_end}.")
        return

    print(f"🧊 Resuming bake from frame {start_frame} to {orig_end} (chunk size {CHUNK}).")
    print(f"Cache directory: {cache_dir}")

    try:
        current = start_frame
        while current <= orig_end:
            chunk_end = min(current + CHUNK - 1, orig_end)

            # Limit scene range for this slice
            scene.frame_start = current
            scene.frame_end = chunk_end
            scene.frame_set(current)

            print(f"➡️  Baking frames {current}–{chunk_end} (cache_type='ALL')...")
            override = {'object': domain_obj}
            result = bpy.ops.fluid.bake_all(override)
            print(f"⬅️  bake_all result: {result}")

            current = chunk_end + 1

    finally:
        # Restore full scene range
        scene.frame_start = orig_start
        scene.frame_end = orig_end
        scene.frame_set(orig_start)

    print("🎉 Bake complete or up to last successful chunk.")


# Run it
bake_all_in_chunks_all_cache()
