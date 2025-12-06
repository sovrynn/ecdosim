#!/usr/bin/env python3
import os
import sys
import argparse
import math
from PIL import Image, ImageOps

# ==========================
# CONFIGURABLE PARAMETERS
# ==========================

FPS = 24  # frames per second # but render at 18.2 fps, this will create the right timing, with 3.5 second song title

# Reverse sequence parameters: multiples of FPS
REVERSE_STAGE1_MULT = 0.8  # initial last-frame hold (brightened)
REVERSE_STAGE2_MULT = 1.6  # reverse zig-zag "windback" (brightened)
REVERSE_STAGE3_MULT = 0.8  # initial first-frame hold (brightened)

# How much to brighten reverse frames toward white (0..1)
REVERSE_BRIGHTEN_FACTOR = 0.5  # 0.5 = halfway to white

# Closing sequence parameters: multiples of FPS
CLOSING_STAGE1_MULT = 1.0  # last-frame darkening (RGB toward black, NOT opacity)

# Rotating radius marker settings (Closing Stage 2)
ANGLE_DEGREES_PER_FRAME = 5.0        # clockwise rotation per frame
BASE_RADIUS_PER_FRAME = 2.0          # base radius growth per frame
BASE_THICKNESS = 2.0                 # base thickness in pixels
RADIUS_RADIUS_MULTIPLIER = 1.05      # multiplies radius every frame
RADIUS_THICKNESS_MULTIPLIER = 1.1   # multiplies thickness every frame

# Input assumptions
INPUT_WIDTH  = 2538
INPUT_HEIGHT = 1080

# Output geometry / crop + pad
CROP_LEFT   = 5
CROP_RIGHT  = 5
TARGET_WIDTH  = INPUT_WIDTH - CROP_LEFT - CROP_RIGHT  # 2528
TARGET_HEIGHT = 1422
PADDING_COLOR_RGB = (0, 0, 0)  # black

# Safety cap for stage 2 (avoid infinite loops)
MAX_FRAMES_STAGE2 = 5000


# ==========================
# HELPER FUNCTIONS
# ==========================

def debug(msg: str):
    print(msg, flush=True)


def list_input_frames(input_dir):
    files = [f for f in os.listdir(input_dir) if f.lower().endswith(".png")]
    if not files:
        raise RuntimeError(f"No PNG files found in {input_dir}")

    def key_fn(name):
        base = os.path.splitext(name)[0]
        try:
            return int(base)
        except ValueError:
            return base

    files.sort(key=key_fn)
    return [os.path.join(input_dir, f) for f in files]


def ensure_output_dir(input_dir):
    parent = os.path.dirname(os.path.abspath(input_dir))
    base_name = os.path.basename(os.path.abspath(input_dir))
    out_dir = os.path.join(parent, base_name + "-edited")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def preprocess_image(img: Image.Image) -> Image.Image:
    """
    Crop left/right to 2528px, pad top/bottom to 1422px, convert to RGBA.
    """
    img = img.convert("RGBA")
    w, h = img.size

    # Crop sides
    left = CROP_LEFT
    right = w - CROP_RIGHT
    img = img.crop((left, 0, right, h))

    # Pad top/bottom
    w2, h2 = img.size
    pad_total = TARGET_HEIGHT - h2
    if pad_total < 0:
        raise RuntimeError(f"TARGET_HEIGHT ({TARGET_HEIGHT}) smaller than cropped height ({h2}).")
    pad_top = pad_total // 2
    pad_bottom = pad_total - pad_top

    fill = (*PADDING_COLOR_RGB, 255)
    img = ImageOps.expand(img, border=(0, pad_top, 0, pad_bottom), fill=fill)
    return img


def load_preprocessed_frame(frame_path: str) -> Image.Image:
    return preprocess_image(Image.open(frame_path))


def brighten_to_white_factor(img: Image.Image, factor: float) -> Image.Image:
    """
    Brighten image toward white by mixing with 255 using factor.
    factor=0 → unchanged
    factor=0.5 → halfway to white
    factor=1.0 → full white
    """
    img = img.convert("RGBA")
    r, g, b, a = img.split()

    def mix_with_white(channel):
        return channel.point(lambda v: int(v * (1 - factor) + 255 * factor))

    r = mix_with_white(r)
    g = mix_with_white(g)
    b = mix_with_white(b)
    return Image.merge("RGBA", (r, g, b, a))


def darken_image_rgb(img: Image.Image, factor: float) -> Image.Image:
    """
    Darken RGB toward black by factor (1.0 = original, 0.5 = halfway to black).
    Alpha is preserved.
    """
    img = img.convert("RGBA")
    r, g, b, a = img.split()
    r = r.point(lambda v: int(v * factor))
    g = g.point(lambda v: int(v * factor))
    b = b.point(lambda v: int(v * factor))
    return Image.merge("RGBA", (r, g, b, a))


def save_frame(img: Image.Image, out_dir: str, frame_index: int):
    img.save(os.path.join(out_dir, f"{frame_index:04d}.png"), format="PNG")


def generate_reverse_stage2_indices(num_input: int, stage2_frames: int):
    """
    Reverse zig-zag selection as described: go back 2 intervals, forward 1, back 2, etc.
    """
    if stage2_frames <= 0:
        return []

    interval = float(num_input) / float(stage2_frames)
    indices = []
    current_anchor = float(num_input)

    while len(indices) < stage2_frames:
        # back two intervals
        p1 = current_anchor - 2.0 * interval
        indices.append(p1)
        if len(indices) >= stage2_frames:
            break

        # forward one interval from p1
        p2 = p1 + interval
        indices.append(p2)
        if len(indices) >= stage2_frames:
            break

        # backward two intervals from p2
        p3 = p2 - 2.0 * interval
        indices.append(p3)
        if len(indices) >= stage2_frames:
            break

        # next group anchor: back two intervals from p3
        current_anchor = p3 - 2.0 * interval
        if current_anchor < 1:
            break

    # Convert to valid 1-based integer indices
    int_indices = []
    for p in indices:
        idx = int(round(p))
        if idx < 1:
            idx = 1
        if idx > num_input:
            idx = num_input
        int_indices.append(idx)
        if len(int_indices) == stage2_frames:
            break

    while len(int_indices) < stage2_frames:
        int_indices.append(1)

    return int_indices


# ==========================
# MAIN SEQUENCE FUNCTIONS
# ==========================

def run_reverse_sequence(input_paths, out_dir, start_frame_index):
    num_input = len(input_paths)
    idx = start_frame_index

    # Stage 1: hold last frame, brightened toward white
    frames_stage1 = int(FPS * REVERSE_STAGE1_MULT)
    if frames_stage1 > 0:
        debug(f"\n=== Reverse Stage 1 (brighten last frame, {REVERSE_BRIGHTEN_FACTOR*100:.0f}% to white) - {frames_stage1} frames ===")
        img_last = brighten_to_white_factor(load_preprocessed_frame(input_paths[-1]), REVERSE_BRIGHTEN_FACTOR)
        for _ in range(frames_stage1):
            save_frame(img_last, out_dir, idx)
            debug(f"  Reverse Stage 1 - output {idx:04d} from input frame {num_input}")
            idx += 1

    # Stage 2: reverse zig-zag, brightened toward white
    frames_stage2 = int(FPS * REVERSE_STAGE2_MULT)
    if frames_stage2 > 0:
        debug(f"\n=== Reverse Stage 2 (brightened zig-zag) - {frames_stage2} frames ===")
        for inp_idx in generate_reverse_stage2_indices(num_input, frames_stage2):
            img = brighten_to_white_factor(load_preprocessed_frame(input_paths[inp_idx - 1]), REVERSE_BRIGHTEN_FACTOR)
            save_frame(img, out_dir, idx)
            debug(f"  Reverse Stage 2 - output {idx:04d} from input frame {inp_idx}")
            idx += 1

    # Stage 3: hold first frame, brightened toward white
    frames_stage3 = int(FPS * REVERSE_STAGE3_MULT)
    if frames_stage3 > 0:
        debug(f"\n=== Reverse Stage 3 (brighten first frame, {REVERSE_BRIGHTEN_FACTOR*100:.0f}% to white) - {frames_stage3} frames ===")
        img_first = brighten_to_white_factor(load_preprocessed_frame(input_paths[0]), REVERSE_BRIGHTEN_FACTOR)
        for _ in range(frames_stage3):
            save_frame(img_first, out_dir, idx)
            debug(f"  Reverse Stage 3 - output {idx:04d} from input frame 1")
            idx += 1

    return idx


def run_original_sequence(input_paths, out_dir, start_frame_index):
    idx = start_frame_index
    debug(f"\n=== Original Sequence (unaltered frames) - {len(input_paths)} frames ===")
    for i, path in enumerate(input_paths, start=1):
        img = load_preprocessed_frame(path)
        save_frame(img, out_dir, idx)
        debug(f"  Original - output {idx:04d} from input frame {i}")
        idx += 1
    return idx


def whiten_pixel_if_needed(px, x, y, w, h, remaining_ref):
    if 0 <= x < w and 0 <= y < h:
        r, g, b, a = px[x, y]
        if not (r == 255 and g == 255 and b == 255):
            px[x, y] = (255, 255, 255, a)
            remaining_ref[0] -= 1


def run_closing_sequence(input_paths, out_dir, start_frame_index):
    num_input = len(input_paths)
    idx = start_frame_index

    base_last = load_preprocessed_frame(input_paths[-1])

    # Stage 1: darken last frame toward black (RGB)
    frames_stage1 = int(FPS * CLOSING_STAGE1_MULT)
    if frames_stage1 > 0:
        debug(f"\n=== Closing Stage 1 (darken last frame toward black) - {frames_stage1} frames ===")
        for i in range(frames_stage1):
            t = i / (frames_stage1 - 1) if frames_stage1 > 1 else 0.0
            factor = 1.0 - 0.5 * t
            img = darken_image_rgb(base_last, factor)
            save_frame(img, out_dir, idx)
            debug(f"  Closing Stage 1 - output {idx:04d} from input frame {num_input} (factor={factor:.3f})")
            idx += 1

    # Stage 2: rotating, growing radius marker, whitening pixels
    debug(f"\n=== Closing Stage 2 (rotating radius marker to full white) ===")

    img = darken_image_rgb(base_last, 0.5)
    px = img.load()
    w, h = img.size

    # Count non-white pixels
    remaining = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if not (r == 255 and g == 255 and b == 255):
                remaining += 1
    remaining_ref = [remaining]

    cx, cy = w // 2, h // 2

    # First frame: center 2x2 white
    for dy in [0, 1]:
        for dx in [0, 1]:
            whiten_pixel_if_needed(px, cx - 1 + dx, cy - 1 + dy, w, h, remaining_ref)

    save_frame(img, out_dir, idx)
    debug(
        f"  Closing Stage 2 - output {idx:04d} (center 2x2 white, remaining={remaining_ref[0]})"
    )
    idx += 1

    # Precompute max radius = image diagonal, to clamp radius
    max_radius = math.hypot(w, h)

    frame_in_stage2 = 1
    while remaining_ref[0] > 0 and frame_in_stage2 < MAX_FRAMES_STAGE2:
        # Compute angle, direction, and perpendicular
        angle_deg = -ANGLE_DEGREES_PER_FRAME * frame_in_stage2  # clockwise
        angle_rad = math.radians(angle_deg)
        dx_dir = math.cos(angle_rad)
        dy_dir = math.sin(angle_rad)
        perp_dx = -dy_dir
        perp_dy = dx_dir

        # Exponential radius and thickness growth
        raw_radius = BASE_RADIUS_PER_FRAME * frame_in_stage2 * (RADIUS_RADIUS_MULTIPLIER ** frame_in_stage2)
        radius = min(raw_radius, max_radius)   # <-- CLAMPED TO DIAGONAL
        thickness = BASE_THICKNESS * (RADIUS_THICKNESS_MULTIPLIER ** frame_in_stage2)

        steps = max(int(radius), 1)
        half_t = thickness / 2.0
        max_offset = max(1, int(math.ceil(half_t)))

        for s in range(steps):
            bx = cx + dx_dir * s
            by = cy + dy_dir * s

            # Sample ALL integer offsets across thickness band
            for offset_step in range(-max_offset, max_offset + 1):
                offset = float(offset_step)
                x = int(round(bx + perp_dx * offset))
                y = int(round(by + perp_dy * offset))
                whiten_pixel_if_needed(px, x, y, w, h, remaining_ref)

        save_frame(img, out_dir, idx)
        debug(
            f"  Closing Stage 2 - output {idx:04d} (n={frame_in_stage2}, radius={radius:.2f}, "
            f"thickness={thickness:.2f}, angle={angle_deg:.1f}°, remaining={remaining_ref[0]})"
        )
        idx += 1
        frame_in_stage2 += 1

    # Force full white if still not done (safety)
    if remaining_ref[0] > 0:
        debug(
            f"  [warn] Closing Stage 2 hit safety cap with {remaining_ref[0]} pixels left, forcing full white."
        )
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if not (r == 255 and g == 255 and b == 255):
                    px[x, y] = (255, 255, 255, a)
        save_frame(img, out_dir, idx)
        debug(f"  Closing Stage 2 - output {idx:04d} (forced full white)")
        idx += 1

    return idx


# ==========================
# MAIN
# ==========================

def main():
    parser = argparse.ArgumentParser(description="Generate edited PNG frame sequence from input directory.")
    parser.add_argument("input_dir", help="Directory with input PNG files named XXXX.png.")
    args = parser.parse_args()

    input_dir = args.input_dir
    if not os.path.isdir(input_dir):
        print(f"Error: '{input_dir}' is not a directory or does not exist.", file=sys.stderr)
        sys.exit(1)

    debug(f"Input directory: {input_dir}")
    input_paths = list_input_frames(input_dir)
    debug(f"Found {len(input_paths)} input frames.")
    out_dir = ensure_output_dir(input_dir)
    debug(f"Output directory: {out_dir}")

    frame_index = 1
    frame_index = run_reverse_sequence(input_paths, out_dir, frame_index)
    frame_index = run_original_sequence(input_paths, out_dir, frame_index)
    frame_index = run_closing_sequence(input_paths, out_dir, frame_index)

    debug(f"\nDone. Total output frames: {frame_index - 1}")
    debug(f"Frames written to: {out_dir}")


if __name__ == "__main__":
    main()
