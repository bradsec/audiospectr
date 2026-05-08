from __future__ import annotations
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def apply_glow(
    image: Image.Image,
    intensity: float = 1.5,
    radius: int = 15,
    scale: float = 0.5,
) -> Image.Image:
    source = image.convert("RGBA")
    bbox = source.getchannel("A").getbbox()
    if bbox is None:
        return source

    pad = max(2, int(radius * 3))
    left = max(0, bbox[0] - pad)
    top = max(0, bbox[1] - pad)
    right = min(source.width, bbox[2] + pad)
    bottom = min(source.height, bbox[3] + pad)
    crop = source.crop((left, top, right, bottom))

    glow_crop = _blur_glow_crop(crop, intensity=intensity, radius=radius, scale=scale)
    result = source.copy()
    result.alpha_composite(glow_crop, (left, top))
    return result


def _blur_glow_crop(
    source: Image.Image,
    intensity: float,
    radius: int,
    scale: float,
) -> Image.Image:
    if scale < 1.0 and source.width * source.height > 65536:
        scale = max(0.1, scale)
        small_size = (
            max(1, int(source.width * scale)),
            max(1, int(source.height * scale)),
        )
        glow_source = source.resize(small_size, Image.Resampling.BILINEAR)
        blurred = glow_source.filter(ImageFilter.GaussianBlur(max(1, radius * scale)))
        blurred = blurred.resize(source.size, Image.Resampling.BILINEAR)
    else:
        blurred = source.filter(ImageFilter.GaussianBlur(radius))
    glow = ImageEnhance.Brightness(blurred).enhance(intensity)
    return glow


def apply_grain(image: Image.Image, intensity: float = 0.05) -> Image.Image:
    arr   = np.array(image, dtype=np.float32)
    noise = np.random.normal(0, intensity * 255, arr[:, :, :3].shape)
    arr[:, :, :3] = np.clip(arr[:, :, :3] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), image.mode)


def apply_blur(image: Image.Image, radius: float) -> Image.Image:
    return image.filter(ImageFilter.GaussianBlur(radius))
