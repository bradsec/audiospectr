import numpy as np
from PIL import Image
from app.layers.circular import CircularLayer
from app.layers.base import aggregate_spectrum as _aggregate_spectrum
from app.audio import FrameData
from app.config import ProjectConfig


def make_frame():
    return FrameData(
        spectrum=np.random.rand(1025).astype(np.float32),
        waveform=np.zeros(735), rms=0.5,
        bass=0.3, mid=0.4, high=0.2,
        sample_rate=22050, frame_index=0, total_frames=30,
    )


def test_circular_render_returns_rgba():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = CircularLayer({"width": 400, "height": 400}, project)
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (400, 400)


def test_circular_renders_pixels():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = CircularLayer({"width": 400, "height": 400, "bar_count": 32}, project)
    result = layer.render(make_frame())
    pixels = np.array(result)
    assert pixels[:, :, 3].max() > 0
    assert tuple(pixels[pixels[:, :, 3] > 0][0][:3]) == (255, 255, 255)


def test_circular_amplitude_scale_makes_low_values_visible():
    spectrum = np.ones(1025, dtype=np.float32) * 0.06
    frame = make_frame()
    frame.spectrum = spectrum
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    flat = CircularLayer(
        {
            "width": 400,
            "height": 400,
            "bar_count": 32,
            "amplitude_scale": 1.0,
            "response_curve": 1.0,
            "min_bar_length": 1,
        },
        project,
    )
    boosted = CircularLayer(
        {
            "width": 400,
            "height": 400,
            "bar_count": 32,
            "amplitude_scale": 5.0,
            "response_curve": 1.0,
            "min_bar_length": 1,
        },
        project,
    )
    flat_pixels = np.array(flat.render(frame))[:, :, 3]
    boosted_pixels = np.array(boosted.render(frame))[:, :, 3]
    assert np.count_nonzero(boosted_pixels) > np.count_nonzero(flat_pixels)


def test_circular_aggregate_spectrum_uses_frequency_windows():
    spectrum = np.zeros(1025)
    spectrum[60:90] = 0.7
    values = _aggregate_spectrum(spectrum, 32)
    assert values.shape == (32,)
    assert values.max() > 0.5


def test_circular_center_image_small_canvas_no_crash():
    """CircularLayer must not crash when inner_radius would produce d<=0."""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
        img.save(f.name)
        center_path = f.name

    try:
        project = ProjectConfig(audio="a.mp3", output="o.mp4", resolution=(30, 30))
        # radius defaults to min(30,30)//3 = 10; inner_radius = 10//2 = 5 → d = 5*2-10 = 0
        layer = CircularLayer({"center_image": center_path}, project)
        fd = FrameData(
            spectrum=np.ones(1025, dtype=np.float32) * 0.5,
            waveform=np.zeros(735),
            rms=0.5, bass=0.5, mid=0.3, high=0.1,
            sample_rate=22050, frame_index=0, total_frames=1,
        )
        result = layer.render(fd)
        assert result.size == (30, 30)
    finally:
        os.unlink(center_path)
