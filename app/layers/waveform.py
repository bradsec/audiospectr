from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw, ImageColor
from scipy.interpolate import make_interp_spline
from app.layers.base import BaseLayer
from app.audio import FrameData
from app.config import ProjectConfig


class WaveformLayer(BaseLayer):
    def __init__(self, config: dict, project: ProjectConfig) -> None:
        super().__init__(config, project)
        self._prev_waveform: np.ndarray | None = None

    def render(self, frame_data: FrameData) -> Image.Image:
        surface = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(surface)

        raw  = frame_data.waveform.astype(np.float64)
        smoothing = float(self.config.get("smoothing_factor", 0.65))
        if self._prev_waveform is not None and self._prev_waveform.shape == raw.shape:
            wave = smoothing * self._prev_waveform + (1.0 - smoothing) * raw
        else:
            wave = raw
        self._prev_waveform = wave

        color       = self.config.get("color", "#ffffff")
        line_width  = int(self.config.get("line_width", 2))
        fill_color  = self.config.get("fill_color")

        rgba = _hex_to_rgba(color)
        points = _waveform_points(wave, self.width, self.height)

        if fill_color:
            fill_rgba = _hex_to_rgba(fill_color, alpha=120)
            base_y    = self.height // 2
            poly      = [(0, base_y)] + points + [(self.width - 1, base_y)]
            draw.polygon(poly, fill=fill_rgba)

        if len(points) >= 2:
            draw.line(points, fill=rgba, width=line_width, joint="curve")

        return surface


def _hex_to_rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)


def _waveform_points(
    wave: np.ndarray, width: int, height: int, n_points: int = 300
) -> list[tuple[int, int]]:
    if len(wave) < 4:
        return []

    # Downsample/resample to n_points using cubic spline
    x_orig  = np.linspace(0, 1, len(wave))
    x_dense = np.linspace(0, 1, n_points)
    try:
        spline = make_interp_spline(x_orig, wave, k=3)
        y_smooth = spline(x_dense)
    except ValueError:
        y_smooth = np.interp(x_dense, x_orig, wave)

    # Clamp to [-1, 1] and map to pixel coords
    y_smooth = np.clip(y_smooth, -1.0, 1.0)
    cx = np.linspace(0, width - 1, n_points).astype(int)
    cy = ((1.0 - y_smooth) * 0.5 * height).astype(int)
    cy = np.clip(cy, 0, height - 1)

    return list(zip(cx.tolist(), cy.tolist()))
