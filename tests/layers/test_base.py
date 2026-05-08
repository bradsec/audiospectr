import numpy as np
import pytest
from app.layers.base import BaseLayer
from app.audio import FrameData
from app.config import ProjectConfig
from PIL import Image


def make_project():
    return ProjectConfig(audio="x.mp3", output="o.mp4")


def make_frame(spectrum=None):
    if spectrum is None:
        spectrum = np.zeros(1025)
    return FrameData(
        spectrum=spectrum,
        waveform=np.zeros(735),
        rms=0.0, bass=0.0, mid=0.0, high=0.0,
        sample_rate=22050, frame_index=0, total_frames=30,
    )


class ConcreteLayer(BaseLayer):
    def render(self, frame_data: FrameData) -> Image.Image:
        return Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))


def test_layer_dimensions_default_to_project_resolution():
    layer = ConcreteLayer({}, make_project())
    assert layer.width == 1920
    assert layer.height == 1080


def test_layer_dimensions_from_config():
    layer = ConcreteLayer({"width": 400, "height": 200}, make_project())
    assert layer.width == 400
    assert layer.height == 200


def test_smooth_spectrum_average():
    layer = ConcreteLayer(
        {"smoothing_type": "average", "smoothing_factor": 0.5},
        make_project(),
    )
    prev = np.ones(1025) * 0.8
    layer._prev_spectrum = prev.copy()
    current = np.zeros(1025)
    result = layer.smooth_spectrum(current)
    expected = 0.5 * prev + 0.5 * current
    np.testing.assert_allclose(result, expected)


def test_smooth_spectrum_linear_decrease():
    layer = ConcreteLayer(
        {"smoothing_type": "linear_decrease", "max_decrease": 0.1},
        make_project(),
    )
    layer._prev_spectrum = np.ones(1025) * 0.5
    current = np.zeros(1025)
    result = layer.smooth_spectrum(current)
    assert np.all(result >= 0.4 - 1e-9)


def test_smooth_spectrum_proportional_decrease():
    layer = ConcreteLayer(
        {"smoothing_type": "proportional_decrease", "smoothing_factor": 0.5},
        make_project(),
    )
    layer._prev_spectrum = np.ones(1025) * 0.8
    current = np.zeros(1025)
    result = layer.smooth_spectrum(current)
    # When current < prev, result = prev * factor = 0.8 * 0.5 = 0.4
    np.testing.assert_allclose(result, np.ones(1025) * 0.4)


def test_get_spectrum_slice_returns_subset():
    layer = ConcreteLayer(
        {"analyzer_range": [20, 250]},
        make_project(),
    )
    spectrum = np.ones(1025)
    sliced = layer.get_spectrum_slice(spectrum, sample_rate=22050)
    assert len(sliced) < 1025
    assert len(sliced) > 0


def test_aggregate_spectrum_available_from_base():
    from app.layers.base import aggregate_spectrum
    spec = np.linspace(0, 1, 100, dtype=np.float32)
    result = aggregate_spectrum(spec, 10)
    assert len(result) == 10
    assert result.dtype == np.float32
    assert result.min() >= 0.0
    assert result.max() <= 1.0


def test_aggregate_spectrum_empty():
    from app.layers.base import aggregate_spectrum
    result = aggregate_spectrum(np.array([]), 0)
    assert len(result) == 0


def test_aggregate_spectrum_fewer_bins_than_bars():
    from app.layers.base import aggregate_spectrum
    spec = np.array([0.1, 0.5, 0.9], dtype=np.float32)
    result = aggregate_spectrum(spec, 10)
    assert len(result) == 3  # can't have more bars than spectrum bins


def test_get_spectrum_slice_caches_freq_mask(mocker):
    """fft_frequencies should only be called once across multiple render calls."""
    import librosa
    from app.config import BackgroundConfig

    mock_fft_freqs = mocker.patch("app.layers.base.librosa.fft_frequencies",
                                   wraps=librosa.fft_frequencies)

    project = ProjectConfig(audio="a.mp3", output="o.mp4",
                            background=BackgroundConfig())
    layer = ConcreteLayer({}, project)
    spectrum = np.random.rand(1025).astype(np.float32)

    for _ in range(5):
        layer.get_spectrum_slice(spectrum, 44100)

    assert mock_fft_freqs.call_count == 1
