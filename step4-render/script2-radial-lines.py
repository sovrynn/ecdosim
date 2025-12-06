import sys
import math
import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

def read_image_any_format(path):
    """Read image via OpenCV, fallback to Pillow for TIFF and other formats."""
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        try:
            pil_img = Image.open(path).convert("RGB")
            img = np.array(pil_img)[:, :, ::-1]  # RGB → BGR
        except Exception as e:
            print(f"Error reading image {path}: {e}")
            sys.exit(1)
    return img

def main():
    if len(sys.argv) < 4:
        print("Usage: python radial_projection.py <image_path> <x_mult> <y_mult> [thickness]")
        print("Example: python radial_projection.py image.tif 0.25 -0.5 5")
        sys.exit(1)

    image_path = sys.argv[1]
    x_mult = float(sys.argv[2])
    y_mult = float(sys.argv[3])
    thickness = int(sys.argv[4]) if len(sys.argv) > 4 else 2

    # Load image
    img = read_image_any_format(image_path)
    h, w = img.shape[:2]
    output = img.copy()

    # Image center as origin
    cx, cy = w / 2, h / 2

    # Convert fractional input into pixel coordinates
    # Positive y_mult means upward (Cartesian style)
    x0 = cx + (x_mult * w / 2)
    y0 = cy - (y_mult * h / 2)

    # Compute hypotenuse (max radius) from this point to origin
    dx = x0 - cx
    dy = y0 - cy
    max_r = math.hypot(dx, dy)

    # Radii for arcs (relative to that distance)
    num_lines = 50
    multiple_distance = 5
    angles = np.linspace(0, 2 * math.pi, num_lines, endpoint=False)
    radii = np.linspace(max_r * 0.2, max_r * multiple_distance, num_lines)

    # Show coordinate info
    print(f"Image size: {w}x{h}")
    print(f"Center (origin): ({cx:.1f}, {cy:.1f})")
    print(f"Input fractions: x_mult={x_mult}, y_mult={y_mult}")
    print(f"Computed pixel center: ({x0:.1f}, {y0:.1f})")
    print(f"Max radius (hypotenuse to origin): {max_r:.1f}px")

    # Draw with progress bar
    with tqdm(total=num_lines * 2, desc="Drawing", ncols=70) as pbar:
        # for angle in angles:
        #     x_end = int(x0 + max_r * math.cos(angle))
        #     y_end = int(y0 - max_r * math.sin(angle))
        #     cv2.line(output, (int(x0), int(y0)), (x_end, y_end), (0, 0, 255), thickness)
        #     pbar.update(1)

        for r in radii:
            cv2.ellipse(output, (int(x0), int(y0)), (int(r), int(r)), 0, 0, 360, (0, 255, 0), thickness - 1)
            pbar.update(1)

    # Mark the point center
    cv2.circle(output, (int(x0), int(y0)), thickness + 2, (255, 0, 0), -1)

    out_path = "output.png"
    cv2.imwrite(out_path, output)
    print(f"\n✅ Output saved to {out_path}")

if __name__ == "__main__":
    main()
