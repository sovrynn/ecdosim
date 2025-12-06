#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from PIL import Image

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def progress_bar(i: int, n: int, width: int = 40):
    filled = int((i / n) * width) if n else 0
    bar = "#" * filled + "-" * (width - filled)
    pct = (i / n * 100.0) if n else 100.0
    sys.stdout.write(f"\r[{bar}] {i}/{n} ({pct:5.1f}%)")
    sys.stdout.flush()

def concat_side_by_side(img_left: Image.Image, img_right: Image.Image) -> Image.Image:
    if img_left.size != img_right.size:
        raise ValueError(f"Image sizes differ: {img_left.size} vs {img_right.size}")
    w, h = img_left.size
    mode = "RGBA" if ("A" in img_left.getbands() or "A" in img_right.getbands()) else "RGB"
    combined = Image.new(mode, (w * 2, h))
    combined.paste(img_left.convert(mode), (0, 0))
    combined.paste(img_right.convert(mode), (w, 0))
    return combined

def main():
    parser = argparse.ArgumentParser(
        description="Combine same-named PNGs from two sibling folders side-by-side."
    )
    parser.add_argument("folder1", help="Relative path to first folder (left image).")
    parser.add_argument("folder2", help="Relative path to second folder (right image).")
    args = parser.parse_args()

    dir1 = Path(args.folder1).resolve()
    dir2 = Path(args.folder2).resolve()

    # Validate directories
    if not dir1.is_dir():
        eprint(f"Error: '{dir1}' is not a directory.")
        sys.exit(1)
    if not dir2.is_dir():
        eprint(f"Error: '{dir2}' is not a directory.")
        sys.exit(1)

    # Ensure they share the same parent
    if dir1.parent != dir2.parent:
        eprint("Error: input directories are not in the same parent folder.")
        eprint(f"Parent 1: {dir1.parent}")
        eprint(f"Parent 2: {dir2.parent}")
        sys.exit(1)

    parent_dir = dir1.parent
    out_dir_name = dir1.name + dir2.name
    out_dir = parent_dir / out_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)

    # Collect PNG filenames
    def png_names(folder: Path):
        return {f.name for f in folder.iterdir() if f.is_file() and f.suffix.lower() == ".png"}

    names1 = png_names(dir1)
    names2 = png_names(dir2)
    common = sorted(names1 & names2)

    if not common:
        eprint("No matching PNG filenames found in both folders.")
        sys.exit(2)

    total = len(common)
    print(f"Found {total} matching PNG(s). Output => {out_dir}")
    processed = 0

    for idx, fname in enumerate(common, start=1):
        left_path = dir1 / fname
        right_path = dir2 / fname

        try:
            with Image.open(left_path) as left_img, Image.open(right_path) as right_img:
                if left_img.size != right_img.size:
                    raise ValueError(
                        f"Resolution mismatch for '{fname}': {left_img.size} vs {right_img.size}"
                    )
                combined = concat_side_by_side(left_img, right_img)
                combined.save(out_dir / fname, format="PNG", compress_level=6, optimize=True)
        except Exception as ex:
            eprint(f"\nError processing '{fname}': {ex}")

        processed += 1
        progress_bar(processed, total)

    print("\nDone.")

if __name__ == "__main__":
    main()
