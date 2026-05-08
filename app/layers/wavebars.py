from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw, ImageColor
from app.layers.base import BaseLayer
from app.audio import FrameData
from app.config import ProjectConfig


class WaveBarsLayer(BaseLayer):
    def __init__(self, config: dict, project: ProjectConfig) -> None:
        super().__init__(config, project)
        self._prev_values: np.ndarray | None = None

    def render(self, frame_data: FrameData) -> Image.Image:
        surface = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(surface)

        bar_count = int(self.config.get("bar_count", 64))
        if bar_count <= 0:
            return surface

        values = _waveform_envelope(frame_data.waveform, bar_count)
        amplitude_scale = float(self.config.get("amplitude_scale", 2.6))
        response_curve = float(self.config.get("response_curve", 0.9))
        values = np.clip(values * amplitude_scale, 0.0, 1.0)
        if response_curve > 0:
            values = np.power(values, response_curve)

        smoothing = float(self.config.get("smoothing_factor", 0.55))
        if self._prev_values is not None and len(self._prev_values) == len(values):
            values = smoothing * self._prev_values + (1.0 - smoothing) * values
        self._prev_values = values

        color = self.config.get("color", "#ffffff")
        reflect_alpha = int(self.config.get("reflection_alpha", 170))
        r, g, b = ImageColor.getrgb(color)

        spacing_ratio = float(self.config.get("spacing_ratio", 0.18))
        total_slot = self.width / bar_count
        _explicit_bar_w = self.config.get("bar_width")
        bar_w = int(_explicit_bar_w if _explicit_bar_w is not None else max(1, round(total_slot * (1.0 - spacing_ratio))))
        corner_radius = int(self.config.get("corner_radius", max(0, bar_w // 3)))
        max_half = self.height * float(self.config.get("height_ratio", 0.34))
        mid_y = self.height // 2
        min_bar_length = int(self.config.get("min_bar_length", 2))

        for i, value in enumerate(values):
            half = max(min_bar_length, int(value * max_half))
            x_center = (i + 0.5) * total_slot
            x0 = int(round(x_center - bar_w / 2))
            x1 = int(round(x_center + bar_w / 2))
            if x1 < 0 or x0 >= self.width:
                continue

            x0 = max(0, x0)
            x1 = min(self.width - 1, x1)
            top = max(0, mid_y - half)
            bottom = min(self.height - 1, mid_y + int(half * 0.9))

            if corner_radius > 0 and half > corner_radius * 2:
                draw.rounded_rectangle([x0, top, x1, mid_y], corner_radius, fill=(r, g, b, 255))
                draw.rounded_rectangle(
                    [x0, mid_y, x1, bottom],
                    corner_radius,
                    fill=(r, g, b, reflect_alpha),
                )
                draw.rectangle([x0, mid_y - corner_radius, x1, mid_y], fill=(r, g, b, 255))
                draw.rectangle([x0, mid_y, x1, mid_y + corner_radius], fill=(r, g, b, reflect_alpha))
            else:
                draw.rectangle([x0, top, x1, mid_y], fill=(r, g, b, 255))
                draw.rectangle([x0, mid_y, x1, bottom], fill=(r, g, b, reflect_alpha))

        return surface


def _waveform_envelope(waveform: np.ndarray, bar_count: int) -> np.ndarray:
    if bar_count <= 0:
        return np.array([], dtype=np.float32)

    wave = np.asarray(waveform, dtype=np.float32)
    if len(wave) == 0:
        return np.zeros(bar_count, dtype=np.float32)

    chunks = np.array_split(np.abs(wave), bar_count)
    values = np.array(
        [float(np.percentile(chunk, 90)) if len(chunk) else 0.0 for chunk in chunks],
        dtype=np.float32,
    )
    return np.clip(values, 0.0, 1.0)
