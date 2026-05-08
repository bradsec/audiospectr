import numpy as np
from app.layers.wavebars import WaveBarsLayer, _waveform_envelope
from app.audio import FrameData
from app.config import ProjectConfig


def make_frame(waveform=None):
    if waveform is None:
        waveform = np.sin(np.linspace(0, 8 * np.pi, 1470)).astype(np.float32)
    return FrameData(
        spectrum=np.zeros(1025),
        waveform=waveform,
        rms=0.5,
        bass=0.3,
        mid=0.4,
        high=0.2,
        sample_rate=22050,
        frame_index=0,
        total_frames=30,
    )


def test_wavebars_render_returns_rgba():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = WaveBarsLayer({"width": 400, "height": 200}, project)
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (400, 200)


def test_wavebars_renders_white_pixels_by_default():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = WaveBarsLayer({"width": 400, "height": 200, "bar_count": 32}, project)
    result = layer.render(make_frame())
    pixels = np.array(result)
    assert pixels[:, :, 3].max() > 0
    assert tuple(pixels[pixels[:, :, 3] > 0][0][:3]) == (255, 255, 255)


def test_wavebars_amplitude_scale_makes_low_values_visible():
    waveform = np.ones(1024, dtype=np.float32) * 0.04
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    flat = WaveBarsLayer(
        {"width": 400, "height": 200, "bar_count": 32, "amplitude_scale": 1.0, "response_curve": 1.0},
        project,
    )
    boosted = WaveBarsLayer(
        {"width": 400, "height": 200, "bar_count": 32, "amplitude_scale": 5.0, "response_curve": 1.0},
        project,
    )
    flat_pixels = np.array(flat.render(make_frame(waveform)))[:, :, 3]
    boosted_pixels = np.array(boosted.render(make_frame(waveform)))[:, :, 3]
    assert np.count_nonzero(boosted_pixels) > np.count_nonzero(flat_pixels)


def test_waveform_envelope_returns_bar_count():
    waveform = np.zeros(1000, dtype=np.float32)
    waveform[100:150] = 0.8
    values = _waveform_envelope(waveform, 40)
    assert values.shape == (40,)
    assert values.max() > 0.7


def test_wavebars_explicit_zero_bar_width_not_coerced():
    """bar_width=0 must not fall back to computed width — should draw 1px-wide bars, not wide ones."""
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    frame = make_frame()
    layer_zero = WaveBarsLayer({"width": 400, "height": 200, "bar_width": 0, "bar_count": 16}, project)
    layer_default = WaveBarsLayer({"width": 400, "height": 200, "bar_count": 16}, project)
    arr_zero = np.array(layer_zero.render(frame))
    arr_default = np.array(layer_default.render(frame))
    assert arr_default[:, :, 3].max() > 0
    zero_pixels = np.count_nonzero(arr_zero[:, :, 3])
    default_pixels = np.count_nonzero(arr_default[:, :, 3])
    assert default_pixels > zero_pixels * 5, (
        f"bar_width=0 coerced to non-zero: {zero_pixels} vs {default_pixels} visible pixels"
    )
