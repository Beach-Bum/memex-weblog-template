"""
Floyd-Steinberg dithering in Python/Pillow — matches the site's
as-dithered-image.js web component output.

Usage:
    from dither import dither_image
    img = dither_image("input.jpg", width=1200, height=630)
    img.save("output.png")
"""
from __future__ import annotations
import numpy as np
from PIL import Image


def dither_image(
    path: str,
    width: int = 1200,
    height: int = 630,
    cutoff: float = 0.5,
    dark: tuple[int, ...] = (0, 0, 0),
    light: tuple[int, ...] = (255, 255, 255),
) -> Image.Image:
    """
    Load an image, crop/resize to target dimensions, convert to grayscale,
    and apply Floyd-Steinberg error-diffusion dithering.

    Returns a PIL Image in RGB mode.
    """
    img = Image.open(path).convert("RGB")

    # Center-crop to target aspect ratio
    w, h = img.size
    target_ratio = width / height
    current_ratio = w / h
    if current_ratio > target_ratio:
        new_w = int(h * target_ratio)
        left = (w - new_w) // 2
        img = img.crop((left, 0, left + new_w, h))
    else:
        new_h = int(w / target_ratio)
        top = (h - new_h) // 2
        img = img.crop((0, top, w, top + new_h))

    img = img.resize((width, height), Image.LANCZOS)

    # Convert to grayscale float array
    gray = np.array(img.convert("L"), dtype=np.float64)

    # Floyd-Steinberg dithering (matching ditherworker.js offsets)
    h, w = gray.shape
    threshold = cutoff * 255

    for y in range(h):
        for x in range(w):
            old = gray[y, x]
            new = 0.0 if old <= threshold else 255.0
            gray[y, x] = new
            err = (old - new) / 8.0
            # Distribute error — same offsets as ditherworker.js
            if x + 1 < w:
                gray[y, x + 1] += err
            if x + 2 < w:
                gray[y, x + 2] += err
            if y + 1 < h:
                if x - 1 >= 0:
                    gray[y + 1, x - 1] += err
                gray[y + 1, x] += err
                if x + 1 < w:
                    gray[y + 1, x + 1] += err
            if y + 2 < h:
                gray[y + 2, x] += err

    # Map to colors
    result = np.zeros((h, w, 3), dtype=np.uint8)
    mask = gray > 127
    result[~mask] = dark[:3]
    result[mask] = light[:3]

    return Image.fromarray(result)


def dither_image_fast(
    path: str,
    width: int = 1200,
    height: int = 630,
    cutoff: float = 0.5,
    dark: tuple[int, ...] = (0, 0, 0),
    light: tuple[int, ...] = (255, 255, 255),
    crunch: int = 3,
) -> Image.Image:
    """
    Faster version: dither at reduced resolution (crunch factor),
    then scale up with nearest-neighbor for chunky pixel look.
    """
    small_w = width // crunch
    small_h = height // crunch
    img = dither_image(path, small_w, small_h, cutoff, dark, light)
    return img.resize((width, height), Image.NEAREST)
