from __future__ import annotations
import math
import numpy as np
from PIL import Image, ImageDraw, ImageColor
from app.layers.base import BaseLayer, aggregate_spectrum
from app.audio import FrameData
from app.config import ProjectConfig


class PulseLayer(BaseLayer):
    def __init__(self, config: dict, project: ProjectConfig) -> None:
        super().__init__(config, project)
        self._rotation = 0.0

    def render(self, frame_data: FrameData) -> Image.Image:
        surface = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(surface)

        base_radius   = int(self.config.get("base_radius", min(self.width, self.height) // 4))
        max_scale     = float(self.config.get("max_scale", 1.6))
        ring_width    = max(1, int(self.config.get("ring_width", 6)))
        color         = self.config.get("color", "#ffffff")
        glow_int      = float(self.config.get("glow_intensity", 1.0))
        ring_count    = max(1, int(self.config.get("ring_count", 3)))
        spoke_count   = max(0, int(self.config.get("spoke_count", 0)))
        spoke_length  = float(self.config.get("spoke_length", 0.28))
        spoke_width   = max(1, int(self.config.get("spoke_width", max(1, ring_width // 2))))
        core_enabled  = bool(self.config.get("core", True))
        core_scale    = float(self.config.get("core_scale", 0.35))
        rotation_speed = float(self.config.get("rotation_speed", 0.15))

        drive  = float(np.clip(frame_data.bass, 0.0, 1.0))
        rms    = float(np.clip(frame_data.rms, 0.0, 1.0))
        radius = int(base_radius * (1.0 + (max_scale - 1.0) * drive))
        if radius <= 0:
            return surface

        cx = self.width  // 2
        cy = self.height // 2

        r_color, g_color, b_color = ImageColor.getrgb(color)
        self._rotation = (self._rotation + math.radians(rotation_speed)) % (2 * math.pi)

        if core_enabled:
            core_radius = max(2, int(base_radius * core_scale * (0.7 + drive)))
            core_alpha = int(np.clip(35 + 90 * rms, 0, 155))
            draw.ellipse(
                [cx - core_radius, cy - core_radius, cx + core_radius, cy + core_radius],
                fill=(r_color, g_color, b_color, core_alpha),
            )

        # Soft outer echoes.
        for i in range(3, 0, -1):
            alpha = int(np.clip(60 * glow_int * drive * (1.0 / i), 0, 255))
            r = radius + i * ring_width * 2
            draw.ellipse(
                [cx - r, cy - r, cx + r, cy + r],
                outline=(r_color, g_color, b_color, alpha),
                width=ring_width,
            )

        # Layered pulse rings.
        for i in range(ring_count):
            offset = i * ring_width * 3
            ring_radius = max(1, radius - offset)
            if ring_radius <= ring_width:
                continue
            alpha = int(np.clip(230 - i * 55 + 25 * drive, 45, 255))
            width = max(1, ring_width - i)
            draw.ellipse(
                [cx - ring_radius, cy - ring_radius, cx + ring_radius, cy + ring_radius],
                outline=(r_color, g_color, b_color, alpha),
                width=width,
            )

        if spoke_count > 0:
            spectrum = self.smooth_spectrum(frame_data.spectrum)
            spectrum = self.get_spectrum_slice(spectrum, frame_data.sample_rate)
            spoke_values = aggregate_spectrum(spectrum, spoke_count)
            spoke_values = np.power(np.clip(spoke_values * 4.0, 0.0, 1.0), 0.65)
            max_spoke = min(self.width, self.height) * spoke_length
            inner = radius + ring_width * 2
            for i, value in enumerate(spoke_values):
                angle = (2 * math.pi * i / spoke_count) + self._rotation
                length = int(max(3, value * max_spoke))
                x1 = cx + inner * math.cos(angle)
                y1 = cy + inner * math.sin(angle)
                x2 = cx + (inner + length) * math.cos(angle)
                y2 = cy + (inner + length) * math.sin(angle)
                alpha = int(np.clip(70 + 175 * value, 0, 245))
                draw.line([(x1, y1), (x2, y2)], fill=(r_color, g_color, b_color, alpha), width=spoke_width)

        alpha_main = int(np.clip(200 + 55 * drive, 0, 255))
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            outline=(r_color, g_color, b_color, alpha_main),
            width=ring_width,
        )

        return surface
