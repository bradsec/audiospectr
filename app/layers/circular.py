from __future__ import annotations
import math
import numpy as np
from PIL import Image, ImageDraw, ImageColor
from app.layers.base import BaseLayer, aggregate_spectrum
from app.audio import FrameData
from app.config import ProjectConfig


class CircularLayer(BaseLayer):
    def __init__(self, config: dict, project: ProjectConfig) -> None:
        super().__init__(config, project)
        self._rotation: float = 0.0

    def render(self, frame_data: FrameData) -> Image.Image:
        surface = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(surface)

        spectrum = self.smooth_spectrum(frame_data.spectrum)
        spectrum = self.get_spectrum_slice(spectrum, frame_data.sample_rate)
        if len(spectrum) == 0:
            return surface

        bar_count    = int(self.config.get("bar_count", 88))
        radius       = int(self.config.get("radius", min(self.width, self.height) // 3))
        inner_radius = int(self.config.get("inner_radius", radius // 2))
        bar_w        = int(self.config.get("bar_width", 6))
        color        = self.config.get("color", "#ffffff")
        rot_speed    = float(self.config.get("rotation_speed", 0.5))
        amplitude_scale = float(self.config.get("amplitude_scale", 4.0))
        response_curve  = float(self.config.get("response_curve", 0.55))
        min_bar_length  = int(self.config.get("min_bar_length", 4))
        rgba         = _hex_to_rgba(color)

        cx = self.width  // 2
        cy = self.height // 2

        self._rotation = (self._rotation + math.radians(rot_speed)) % (2 * math.pi)

        bar_count = min(bar_count, len(spectrum))
        bar_values = aggregate_spectrum(spectrum, bar_count)
        bar_values = np.clip(bar_values * amplitude_scale, 0.0, 1.0)
        if response_curve > 0:
            bar_values = np.power(bar_values, response_curve)

        if inner_radius >= radius:
            inner_radius = max(1, radius - 1)
        max_bar = radius - inner_radius

        for i, value in enumerate(bar_values):
            angle   = (2 * math.pi * i / bar_count) + self._rotation
            bar_len = max(min_bar_length, int(value * max_bar))

            x1 = cx + inner_radius * math.cos(angle)
            y1 = cy + inner_radius * math.sin(angle)
            x2 = cx + (inner_radius + bar_len) * math.cos(angle)
            y2 = cy + (inner_radius + bar_len) * math.sin(angle)

            draw.line([(x1, y1), (x2, y2)], fill=rgba, width=bar_w)

        center_img = self.config.get("center_image")
        if center_img:
            try:
                cimg = Image.open(center_img).convert("RGBA")
                d    = max(1, inner_radius * 2 - 10)
                cimg = cimg.resize((d, d), Image.LANCZOS)
                surface.paste(cimg, (cx - d // 2, cy - d // 2), cimg)
            except Exception:
                pass

        return surface


# NOTE: _hex_to_rgba is behaviorally identical to _parse_color in bars.py.
# Both call ImageColor.getrgb() and return (r, g, b, 255). Consolidating them
# into base.py or a shared utility is a separate cleanup task.
def _hex_to_rgba(color: str, alpha: int = 255) -> tuple[int, int, int, int]:
    r, g, b = ImageColor.getrgb(color)
    return (r, g, b, alpha)
