import numpy as np
from PIL import Image
from app.effects import apply_glow, apply_grain, apply_blur


def make_rgba(w=100, h=100, color=(255, 0, 0, 255)):
    img = Image.new("RGBA", (w, h), color)
    return img


def test_apply_glow_returns_rgba():
    img = make_rgba()
    result = apply_glow(img, intensity=1.5, radius=5)
    assert result.mode == "RGBA"
    assert result.size == img.size


def test_apply_glow_increases_brightness():
    img = make_rgba(color=(100, 0, 0, 255))
    result = apply_glow(img, intensity=2.0, radius=5)
    arr_in  = np.array(img)
    arr_out = np.array(result)
    assert arr_out[:, :, 0].mean() >= arr_in[:, :, 0].mean()


def test_apply_glow_expands_alpha_beyond_source_shape():
    img = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    img.putpixel((20, 20), (255, 0, 0, 255))
    result = apply_glow(img, intensity=3.0, radius=4)
    assert result.getpixel((20, 20))[3] == 255
    assert result.getpixel((20, 24))[3] > 0


def test_apply_glow_supports_scaled_blur_path():
    img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    img.putpixel((40, 40), (255, 0, 0, 255))
    result = apply_glow(img, intensity=3.0, radius=8, scale=0.25)
    assert result.size == img.size
    assert result.getpixel((40, 40))[3] == 255
    assert result.getpixel((40, 46))[3] > 0


def test_apply_glow_keeps_blank_regions_unchanged():
    img = Image.new("RGBA", (120, 80), (0, 0, 0, 0))
    img.putpixel((60, 40), (255, 0, 0, 255))
    result = apply_glow(img, intensity=3.0, radius=4, scale=0.5)
    assert result.getpixel((0, 0)) == (0, 0, 0, 0)


def test_apply_grain_returns_rgba():
    img = make_rgba()
    result = apply_grain(img, intensity=0.05)
    assert result.mode == "RGBA"
    assert result.size == img.size


def test_apply_grain_adds_noise():
    img = make_rgba(color=(128, 128, 128, 255))
    result = apply_grain(img, intensity=0.2)
    arr_in  = np.array(img)
    arr_out = np.array(result)
    assert not np.array_equal(arr_in[:, :, :3], arr_out[:, :, :3])


def test_apply_blur_returns_same_size():
    img = make_rgba()
    result = apply_blur(img, radius=3)
    assert result.size == img.size


def test_apply_blur_changes_pixels():
    # Use a non-uniform image (checkerboard) so blur actually changes pixel values
    img = Image.new("RGBA", (100, 100), (0, 0, 0, 255))
    pixels = img.load()
    for y in range(100):
        for x in range(100):
            if (x + y) % 2 == 0:
                pixels[x, y] = (200, 50, 50, 255)
    result = apply_blur(img, radius=5)
    arr_in  = np.array(img)
    arr_out = np.array(result.convert("RGBA"))
    assert not np.array_equal(arr_in, arr_out)
