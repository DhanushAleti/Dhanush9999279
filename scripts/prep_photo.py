#!/usr/bin/env python3
"""Prep a portrait for ASCII conversion: strip the background, boost local contrast."""
import io
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

CLIP_LIMIT = 2.5
TILE_GRID_SIZE = (8, 8)
MODEL = "u2net_human_seg"  # person-specific, avoids picking up background objects


def apply_clahe(rgb: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=CLIP_LIMIT, tileGridSize=TILE_GRID_SIZE)
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)


def main():
    if len(sys.argv) != 3:
        print("usage: prep_photo.py <input> <output.png>")
        sys.exit(1)

    src_path, out_path = sys.argv[1], sys.argv[2]

    with open(src_path, "rb") as f:
        input_bytes = f.read()

    print("removing background...")
    session = new_session(MODEL)
    result_bytes = remove(input_bytes, session=session)
    rgba = Image.open(io.BytesIO(result_bytes)).convert("RGBA")

    rgb = np.array(rgba.convert("RGB"))
    alpha = np.array(rgba)[:, :, 3]

    print("boosting local contrast (CLAHE)...")
    contrasted = apply_clahe(rgb)

    out = np.dstack([contrasted, alpha])
    Image.fromarray(out, mode="RGBA").save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
