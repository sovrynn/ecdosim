import bpy

def get_scene_camera(scene):
    """Return the active camera, or the first camera found in the scene."""
    if scene.camera is not None:
        return scene.camera
    
    # Fallback: look for any camera in the scene
    for obj in scene.objects:
        if obj.type == 'CAMERA':
            return obj
    
    return None

def print_camera_keyframes():
    scene = bpy.context.scene
    cam = get_scene_camera(scene)
    
    if cam is None:
        print("No camera found in the scene.")
        return
    
    if cam.animation_data is None or cam.animation_data.action is None:
        print(f"Camera '{cam.name}' has no keyframes (no action).")
        return
    
    action = cam.animation_data.action
    keyframe_frames = set()
    
    # Collect all keyframe frame numbers from all F-Curves
    for fcurve in action.fcurves:
        for kp in fcurve.keyframe_points:
            frame = kp.co[0]  # X coordinate is the frame number
            keyframe_frames.add(int(round(frame)))
    
    # Print the sorted list of frame numbers
    print(f"Keyframes for camera '{cam.name}':")
    for frame in sorted(keyframe_frames):
        print(f"Frame: {frame}")

# Run it
print_camera_keyframes()
