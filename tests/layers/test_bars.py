# tests/layers/test_bars.py
import numpy as np
from PIL import Image
from app.layers.bars import BarsLayer
from app.layers.base import aggregate_spectrum as _aggregate_spectrum
from app.audio import FrameData
from app.config import ProjectConfig


def make_project():
    return ProjectConfig(audio="x.mp3", output="o.mp4")


def make_frame(spectrum=None):
    if spectrum is None:
        spectrum = np.random.rand(1025).astype(np.float32)
    return FrameData(
        spectrum=spectrum, waveform=np.zeros(735),
        rms=0.5, bass=0.3, mid=0.4, high=0.2,
        sample_rate=22050, frame_index=0, total_frames=30,
    )


def test_bars_render_returns_rgba():
    layer = BarsLayer({"width": 200, "height": 100}, make_project())
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (200, 100)


def test_bars_render_draws_pixels():
    layer = BarsLayer({"width": 200, "height": 100, "bar_count": 10}, make_project())
    spectrum = np.ones(1025) * 0.8
    result = layer.render(make_frame(spectrum))
    pixels = np.array(result)
    assert pixels[:, :, 3].max() > 0  # some non-transparent pixels
    assert tuple(pixels[pixels[:, :, 3] > 0][0][:3]) == (255, 255, 255)


def test_bars_mirror_mode_symmetric():
    layer = BarsLayer(
        {"width": 200, "height": 100, "bar_count": 10, "mirror": True},
        make_project(),
    )
    spectrum = np.ones(1025) * 0.8
    result = layer.render(make_frame(spectrum))
    assert result.size == (200, 100)
    arr = np.array(result)
    left  = arr[:, :100, :]
    right = arr[:, 100:, :]
    # Right half should be a mirror of the left half
    np.testing.assert_array_equal(left, right[:, ::-1, :])


def test_bars_silent_frame_produces_empty_or_minimal():
    layer = BarsLayer({"width": 200, "height": 100, "bar_count": 10}, make_project())
    spectrum = np.zeros(1025)
    result = layer.render(make_frame(spectrum))
    assert result.mode == "RGBA"


def test_bars_gradient_with_secondary_color():
    layer = BarsLayer(
        {"width": 200, "height": 100, "bar_count": 10,
         "color": "#00f5ff", "secondary_color": "#ff00cc", "corner_radius": 0},
        make_project(),
    )
    spectrum = np.ones(1025) * 0.8
    result = layer.render(make_frame(spectrum))
    pixels = np.array(result)
    assert pixels[:, :, 3].max() > 0  # has visible pixels
    # Blue channel (index 2) should vary from top to bottom of the bar
    # (top color is #00f5ff = cyan, bottom is #ff00cc = magenta — blue channel differs)
    alpha_col = pixels[:, :, 3]
    for col_idx in range(pixels.shape[1]):
        col_alpha = alpha_col[:, col_idx]
        if col_alpha.max() > 0:
            visible_rows = np.where(col_alpha > 0)[0]
            if len(visible_rows) > 5:
                top_blue    = int(pixels[visible_rows[0],  col_idx, 2])
                bottom_blue = int(pixels[visible_rows[-1], col_idx, 2])
                # cyan (#00f5ff) has blue=255, magenta (#ff00cc) has blue=204
                # so top should have higher blue than bottom
                assert top_blue >= bottom_blue - 10
                break


def test_bars_peak_indicators_draws_pixels():
    layer = BarsLayer(
        {"width": 200, "height": 100, "bar_count": 10, "peak_indicators": True},
        make_project(),
    )
    spectrum = np.ones(1025) * 0.8
    result = layer.render(make_frame(spectrum))
    pixels = np.array(result)
    assert pixels[:, :, 3].max() > 0


def test_bars_amplitude_scale_makes_low_values_visible():
    spectrum = np.ones(1025) * 0.08
    project = make_project()
    flat = BarsLayer(
        {"width": 200, "height": 100, "bar_count": 10, "amplitude_scale": 1.0, "response_curve": 1.0},
        project,
    )
    boosted = BarsLayer(
        {"width": 200, "height": 100, "bar_count": 10, "amplitude_scale": 4.0, "response_curve": 1.0},
        project,
    )
    flat_alpha_rows = np.where(np.array(flat.render(make_frame(spectrum)))[:, :, 3].max(axis=1) > 0)[0]
    boosted_alpha_rows = np.where(np.array(boosted.render(make_frame(spectrum)))[:, :, 3].max(axis=1) > 0)[0]
    assert len(boosted_alpha_rows) > len(flat_alpha_rows)


def test_aggregate_spectrum_uses_frequency_windows():
    spectrum = np.zeros(1025)
    spectrum[80:100] = 0.7
    values = _aggregate_spectrum(spectrum, 32)
    assert values.shape == (32,)
    assert values.max() > 0.5
