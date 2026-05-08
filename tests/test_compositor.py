import numpy as np
from PIL import Image
from unittest.mock import MagicMock
from app.compositor import Compositor, _fit_background_image, _resize_cover
from app.config import ProjectConfig, BackgroundConfig
from app.audio import FrameData
from app.layers.base import BaseLayer


def make_frame(idx=0, total=10):
    return FrameData(
        spectrum=np.zeros(1025), waveform=np.zeros(735),
        rms=0.0, bass=0.0, mid=0.0, high=0.0,
        sample_rate=22050, frame_index=idx, total_frames=total,
    )


class RedLayer(BaseLayer):
    def render(self, frame_data: FrameData) -> Image.Image:
        img = Image.new("RGBA", (self.width, self.height), (255, 0, 0, 255))
        return img


def test_composite_frame_returns_rgb_image():
    project = ProjectConfig(audio="x.mp3", output="o.mp4", resolution=(100, 100))
    comp = Compositor(project, [])
    bg = Image.new("RGB", (100, 100), (0, 0, 0))
    result = comp.composite_frame(make_frame(), bg)
    assert result.mode == "RGB"
    assert result.size == (100, 100)


def test_composite_frame_layers_red_over_black():
    project = ProjectConfig(audio="x.mp3", output="o.mp4", resolution=(100, 100))
    layer = RedLayer({"width": 100, "height": 100}, project)
    comp = Compositor(project, [layer])
    bg = Image.new("RGB", (100, 100), (0, 0, 0))
    result = comp.composite_frame(make_frame(), bg)
    r, g, b = result.getpixel((50, 50))
    assert r == 255
    assert g == 0


def test_compositor_calls_encoder_for_each_frame():
    project = ProjectConfig(audio="x.mp3", output="o.mp4", resolution=(10, 10))
    comp = Compositor(project, [])
    encoder = MagicMock()
    frames = [make_frame(i, 3) for i in range(3)]
    comp.render(frames, encoder)
    assert encoder.write_frame.call_count == 3


def test_composite_frame_opacity_half_red_over_black():
    project = ProjectConfig(audio="x.mp3", output="o.mp4", resolution=(100, 100))
    layer = RedLayer({"width": 100, "height": 100, "opacity": 0.5}, project)
    comp = Compositor(project, [layer])
    bg = Image.new("RGB", (100, 100), (0, 0, 0))
    result = comp.composite_frame(make_frame(), bg)
    r, g, b = result.getpixel((50, 50))
    # 50% opacity red over black should give approximately r=127
    assert 100 <= r <= 160
    assert g == 0


def test_composite_frame_additive_blend():
    project = ProjectConfig(audio="x.mp3", output="o.mp4", resolution=(100, 100))
    # Red layer (128,0,0,255) additive over half-red background (128,0,0)
    # Result should be brighter red (>128), clamped to 255 max
    class HalfRedLayer(BaseLayer):
        def render(self, frame_data):
            return Image.new("RGBA", (self.width, self.height), (128, 0, 0, 255))
    layer = HalfRedLayer({"width": 100, "height": 100, "blend_mode": "add"}, project)
    comp = Compositor(project, [layer])
    bg = Image.new("RGB", (100, 100), (128, 0, 0))
    result = comp.composite_frame(make_frame(), bg)
    r, g, b = result.getpixel((50, 50))
    assert r > 128  # additive should be brighter than background alone
    assert g == 0


def test_composite_frame_screen_blend():
    project = ProjectConfig(audio="x.mp3", output="o.mp4", resolution=(100, 100))

    class GreenLayer(BaseLayer):
        def render(self, frame_data):
            return Image.new("RGBA", (self.width, self.height), (0, 128, 0, 255))

    layer = GreenLayer({"width": 100, "height": 100, "blend_mode": "screen"}, project)
    comp = Compositor(project, [layer])
    bg = Image.new("RGB", (100, 100), (128, 0, 0))
    result = comp.composite_frame(make_frame(), bg)
    r, g, b = result.getpixel((50, 50))
    assert r == 128
    assert g == 128
    assert b == 0


def test_resize_cover_preserves_aspect_ratio_by_cropping():
    src = Image.new("RGB", (200, 100), (255, 0, 0))
    src.putpixel((0, 50), (0, 255, 0))
    src.putpixel((199, 50), (0, 0, 255))
    result = _resize_cover(src, (100, 100))
    assert result.size == (100, 100)
    assert result.getpixel((0, 50)) == (255, 0, 0)
    assert result.getpixel((99, 50)) == (255, 0, 0)


def test_fit_background_image_stretch_fills_canvas():
    src = Image.new("RGB", (50, 100), (255, 0, 0))
    result = _fit_background_image(src, (100, 100), "stretch", (0, 0, 0))
    assert result.size == (100, 100)
    assert result.getpixel((99, 99)) == (255, 0, 0)


def test_fit_background_image_contain_centers_with_padding():
    src = Image.new("RGB", (50, 100), (255, 0, 0))
    result = _fit_background_image(src, (100, 100), "contain", (0, 0, 0))
    assert result.size == (100, 100)
    assert result.getpixel((0, 50)) == (0, 0, 0)
    assert result.getpixel((50, 50)) == (255, 0, 0)


def test_fit_background_image_center_keeps_original_size():
    src = Image.new("RGB", (20, 20), (255, 0, 0))
    result = _fit_background_image(src, (100, 100), "center", (0, 0, 0))
    assert result.size == (100, 100)
    assert result.getpixel((10, 10)) == (0, 0, 0)
    assert result.getpixel((50, 50)) == (255, 0, 0)


def test_compositor_applies_glow_when_configured(mocker):
    mock_glow = mocker.patch("app.compositor.apply_glow", side_effect=lambda img, **kw: img)

    class RedLayer(BaseLayer):
        def render(self, frame_data):
            return Image.new("RGBA", (self.width, self.height), (255, 0, 0, 255))

    project = ProjectConfig(audio="a.mp3", output="o.mp4", resolution=(20, 20), fps=1)
    layer = RedLayer(
        {"effects": {"glow": True, "glow_intensity": 1.0, "glow_radius": 10, "glow_scale": 0.5}},
        project,
    )
    comp = Compositor(project, [layer])
    fd = make_frame()
    bg = Image.new("RGB", (20, 20), (0, 0, 0))
    comp.composite_frame(fd, bg)
    mock_glow.assert_called_once()


def test_compositor_applies_grain_when_configured(mocker):
    mock_grain = mocker.patch("app.compositor.apply_grain", side_effect=lambda img, amt: img)

    class WhiteLayer(BaseLayer):
        def render(self, frame_data):
            return Image.new("RGBA", (self.width, self.height), (255, 255, 255, 255))

    project = ProjectConfig(audio="a.mp3", output="o.mp4", resolution=(20, 20), fps=1)
    layer = WhiteLayer({"effects": {"grain": 0.3}}, project)
    comp = Compositor(project, [layer])
    fd = make_frame()
    bg = Image.new("RGB", (20, 20), (0, 0, 0))
    comp.composite_frame(fd, bg)
    mock_grain.assert_called_once_with(mocker.ANY, 0.3)


def test_compositor_skips_glow_when_not_configured():
    class SimpleLayer(BaseLayer):
        def render(self, frame_data):
            return Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

    project = ProjectConfig(audio="a.mp3", output="o.mp4", resolution=(10, 10), fps=1)
    layer = SimpleLayer({}, project)
    comp = Compositor(project, [layer])
    fd = make_frame()
    bg = Image.new("RGB", (10, 10), (0, 0, 0))
    result = comp.composite_frame(fd, bg)
    assert result is not None
