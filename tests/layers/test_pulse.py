# tests/layers/test_pulse.py
import numpy as np
from PIL import Image
from app.layers.pulse import PulseLayer
from app.layers.base import aggregate_spectrum as _aggregate_spectrum
from app.audio import FrameData
from app.config import ProjectConfig


def make_frame(bass=0.8):
    return FrameData(
        spectrum=np.linspace(0, bass, 1025), waveform=np.zeros(735),
        rms=bass, bass=bass, mid=0.1, high=0.1,
        sample_rate=22050, frame_index=0, total_frames=30,
    )


def test_pulse_render_returns_rgba():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = PulseLayer({"width": 400, "height": 400}, project)
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (400, 400)


def test_pulse_renders_ring():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = PulseLayer({"width": 400, "height": 400}, project)
    result = layer.render(make_frame(bass=0.9))
    pixels = np.array(result)
    assert pixels[:, :, 3].max() > 0
    assert tuple(pixels[pixels[:, :, 3] > 0][0][:3]) == (255, 255, 255)


def test_pulse_silent_frame():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = PulseLayer({"width": 400, "height": 400}, project)
    result = layer.render(make_frame(bass=0.0))
    assert result.mode == "RGBA"
    assert result.size == (400, 400)


def test_pulse_peak_bass():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = PulseLayer({"width": 400, "height": 400}, project)
    result = layer.render(make_frame(bass=1.0))
    pixels = np.array(result)
    assert pixels[:, :, 3].max() > 0


def test_pulse_small_canvas():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = PulseLayer({"width": 50, "height": 50}, project)
    result = layer.render(make_frame(bass=0.8))
    assert result.mode == "RGBA"
    assert result.size == (50, 50)


def test_pulse_spokes_add_more_detail():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    base = PulseLayer({"width": 400, "height": 400, "spoke_count": 0, "ring_count": 1}, project)
    detailed = PulseLayer({"width": 400, "height": 400, "spoke_count": 48, "ring_count": 3}, project)
    frame = make_frame(bass=0.8)
    base_pixels = np.array(base.render(frame))[:, :, 3]
    detailed_pixels = np.array(detailed.render(frame))[:, :, 3]
    assert np.count_nonzero(detailed_pixels) > np.count_nonzero(base_pixels)


def test_pulse_aggregate_spectrum_returns_requested_count():
    spectrum = np.zeros(1025)
    spectrum[50:80] = 0.9
    values = _aggregate_spectrum(spectrum, 32)
    assert values.shape == (32,)
    assert values.max() > 0.8
