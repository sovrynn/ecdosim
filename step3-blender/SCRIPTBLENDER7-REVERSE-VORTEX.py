import bpy

EPS = 1e-12  # treat values close to 0 as zero to avoid tiny float noise

def invert_vortex_strength_keyframes():
    found_any = False

    for obj in bpy.data.objects:
        fld = getattr(obj, "field", None)
        if not fld or fld.type != 'VORTEX':
            continue

        found_any = True
        ad = obj.animation_data
        if not ad:
            print(f"[{obj.name}] No animation data.")
            continue

        action = ad.action
        if not action:
            print(f"[{obj.name}] No active action (keyframes may be in NLA strips).")
            continue

        # Find F-Curves that animate the field strength
        fcurves = [fc for fc in action.fcurves if fc.data_path == "field.strength"]
        if not fcurves:
            print(f"[{obj.name}] No keyframes found for field.strength.")
            continue

        for fc in fcurves:
            for kp in fc.keyframe_points:
                frame = kp.co[0]
                old_val = float(kp.co[1])

                if abs(old_val) > EPS:
                    new_val = -old_val
                    # Update the keyframe value
                    kp.co[1] = new_val
                    # Move handles by the same delta to preserve curve shape locally
                    delta = new_val - old_val
                    kp.handle_left.y += delta
                    kp.handle_right.y += delta

                    print(f"[{obj.name}] frame {int(frame)}: strength {old_val:.6g} -> {new_val:.6g}")
                else:
                    print(f"[{obj.name}] frame {int(frame)}: strength is zero (or ~0); skipped.")

            fc.update()

    # Ensure depsgraph/view layer are aware of changes
    bpy.context.view_layer.update()

    if not found_any:
        print("No VORTEX force fields found in the scene.")

# Run it
invert_vortex_strength_keyframes()
