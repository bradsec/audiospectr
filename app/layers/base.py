from __future__ import annotations
from abc import ABC, abstractmethod
import numpy as np
import librosa
from PIL import Image
from app.audio import FrameData
from app.config import ProjectConfig


class BaseLayer(ABC):
    def __init__(self, config: dict, project: ProjectConfig) -> None:
        w, h = project.resolution
        w_cfg = config.get("width")
        h_cfg = config.get("height")
        self.width: int  = w_cfg if w_cfg is not None else w
        self.height: int = h_cfg if h_cfg is not None else h
        self.x: int      = config.get("x", 0)
        self.y: int      = config.get("y", 0)
        self.opacity: float   = config.get("opacity", 1.0)
        self.blend_mode: str  = config.get("blend_mode", "normal")
        self.config: dict     = config
        self._prev_spectrum   = np.zeros(1025)
        self._freq_mask_cache: dict[int, np.ndarray] = {}

    def smooth_spectrum(self, spectrum: np.ndarray) -> np.ndarray:
        mode   = self.config.get("smoothing_type", "average")
        factor = float(self.config.get("smoothing_factor", 0.8))
        prev   = self._prev_spectrum

        if mode == "average":
            result = factor * prev + (1.0 - factor) * spectrum
        elif mode == "linear_decrease":
            max_dec = float(self.config.get("max_decrease", 0.05))
            result = np.where(
                spectrum >= prev,
                spectrum,
                np.maximum(spectrum, prev - max_dec),
            )
        elif mode == "proportional_decrease":
            result = np.where(spectrum >= prev, spectrum, prev * factor)
        else:
            result = spectrum.copy()

        self._prev_spectrum = result
        return result

    def get_spectrum_slice(
        self, spectrum: np.ndarray, sample_rate: int
    ) -> np.ndarray:
        min_hz, max_hz = self.config.get("analyzer_range", [20, 20000])
        if sample_rate not in self._freq_mask_cache:
            freqs = librosa.fft_frequencies(sr=sample_rate, n_fft=2048)
            self._freq_mask_cache[sample_rate] = (freqs >= min_hz) & (freqs <= max_hz)
        return spectrum[self._freq_mask_cache[sample_rate]]

    @abstractmethod
    def render(self, frame_data: FrameData) -> Image.Image:
        """Return an RGBA PIL Image sized (self.width, self.height)."""


def aggregate_spectrum(spectrum: np.ndarray, bar_count: int) -> np.ndarray:
    if bar_count <= 0:
        return np.array([], dtype=np.float32)
    if len(spectrum) <= bar_count:
        return spectrum.astype(np.float32)

    edges = np.geomspace(1, len(spectrum), bar_count + 1) - 1
    edges = np.unique(np.round(edges).astype(int))
    if len(edges) < bar_count + 1:
        edges = np.linspace(0, len(spectrum), bar_count + 1).astype(int)

    values: list[float] = []
    for start, end in zip(edges[:-1], edges[1:]):
        end = max(end, start + 1)
        window = spectrum[start:end]
        values.append(float(np.percentile(window, 85)) if len(window) > 0 else 0.0)

    if len(values) < bar_count:
        values.extend([0.0] * (bar_count - len(values)))
    return np.array(values[:bar_count], dtype=np.float32)
