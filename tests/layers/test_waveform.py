import numpy as np
from PIL import Image
from app.layers.waveform import WaveformLayer
from app.audio import FrameData
from app.config import ProjectConfig


def make_frame(waveform=None):
    if waveform is None:
        waveform = np.sin(np.linspace(0, 2 * np.pi, 735)).astype(np.float32)
    return FrameData(
        spectrum=np.zeros(1025), waveform=waveform,
        rms=0.5, bass=0.3, mid=0.4, high=0.2,
        sample_rate=22050, frame_index=0, total_frames=30,
    )


def test_waveform_render_returns_rgba():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = WaveformLayer({"width": 200, "height": 100}, project)
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (200, 100)


def test_waveform_renders_something():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = WaveformLayer({"width": 400, "height": 200, "line_width": 3}, project)
    result = layer.render(make_frame())
    pixels = np.array(result)
    assert pixels[:, :, 3].max() > 0
    assert tuple(pixels[pixels[:, :, 3] > 0][0][:3]) == (255, 255, 255)


def test_waveform_fill_color_renders_filled_polygon():
    """WaveformLayer with fill_color must produce visible pixels below the waveform line."""
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = WaveformLayer({"width": 200, "height": 100, "color": "#00ffff", "fill_color": "#003333"}, project)
    t = np.linspace(0, 2 * np.pi, 735)
    wave = (np.sin(t) * 0.5).astype(np.float32)
    result = layer.render(make_frame(wave))
    arr = np.array(result)
    assert arr[:, :, 3].max() > 0, "fill_color produced no visible pixels"
    lower_half = arr[50:, :, 3]
    assert lower_half.max() > 0, "fill_color produced no pixels in lower half of image"
