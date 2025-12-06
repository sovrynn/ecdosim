import sys
import math
import cv2
import numpy as np
from PIL import Image

def read_image_any_format(path):
    """Read image via OpenCV, fallback to Pillow for TIFF."""
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
        print("Usage: python radial_projection.py <image_path> <x> <y>")
        sys.exit(1)

    image_path = sys.argv[1]
    x_in = float(sys.argv[2])
    y_in = float(sys.argv[3])

    # Load image (supports .tif, .tiff, .jpg, .png, etc.)
    img = read_image_any_format(image_path)
    h, w = img.shape[:2]
    output = img.copy()

    # Image center as origin
    cx, cy = w / 2, h / 2
    x0, y0 = cx + x_in, cy - y_in

    # Radial lines and arcs
    num_lines = 5
    angles = np.linspace(0, 2 * math.pi, num_lines, endpoint=False)
    max_r = int(math.hypot(w, h) / 2)
    radii = np.linspace(max_r * 0.2, max_r, num_lines)

    for angle in angles:
        x_end = int(x0 + max_r * math.cos(angle))
        y_end = int(y0 - max_r * math.sin(angle))
        cv2.line(output, (int(x0), int(y0)), (x_end, y_end), (0, 0, 255), 2)

    for r in radii:
        cv2.ellipse(output, (int(x0), int(y0)), (int(r), int(r)), 0, 0, 360, (0, 255, 0), 1)

    cv2.circle(output, (int(x0), int(y0)), 5, (255, 0, 0), -1)

    out_path = "output.png"
    cv2.imwrite(out_path, output)
    print(f"Output saved to {out_path}")

if __name__ == "__main__":
    main()
