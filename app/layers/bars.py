from __future__ import annotations
import numpy as np
from PIL import Image, ImageDraw, ImageColor
from app.layers.base import BaseLayer, aggregate_spectrum
from app.audio import FrameData
from app.config import ProjectConfig


def _parse_color(hex_color: str) -> tuple[int, int, int, int]:
    r, g, b = ImageColor.getrgb(hex_color)
    return (r, g, b, 255)


def _gradient_column(width: int, height: int, top: tuple, bottom: tuple) -> Image.Image:
    t = np.linspace(0, 1, height)[:, np.newaxis]
    top_arr    = np.array(top,    dtype=np.float32)
    bottom_arr = np.array(bottom, dtype=np.float32)
    colors = (1.0 - t) * top_arr + t * bottom_arr
    strip  = np.broadcast_to(colors.astype(np.uint8)[:, np.newaxis, :], (height, width, 4)).copy()
    return Image.fromarray(strip, "RGBA")


class BarsLayer(BaseLayer):
    def __init__(self, config: dict, project: ProjectConfig) -> None:
        super().__init__(config, project)

    def render(self, frame_data: FrameData) -> Image.Image:
        surface = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

        spectrum = self.smooth_spectrum(frame_data.spectrum)
        spectrum = self.get_spectrum_slice(spectrum, frame_data.sample_rate)
        if len(spectrum) == 0:
            return surface

        bar_count     = int(self.config.get("bar_count", 64))
        mirror        = bool(self.config.get("mirror", False))
        corner_radius = int(self.config.get("corner_radius", 4))
        color_top     = _parse_color(self.config.get("color", "#ffffff"))
        secondary     = self.config.get("secondary_color")
        color_bot     = _parse_color(secondary) if secondary else color_top
        peak_on       = bool(self.config.get("peak_indicators", False))
        amplitude_scale = float(self.config.get("amplitude_scale", 3.0))
        response_curve  = float(self.config.get("response_curve", 0.65))

        draw_width = self.width // 2 if mirror else self.width
        spacing    = int(self.config.get("spacing", 2))
        bar_w      = self.config.get("bar_width") or max(
            1, (draw_width - spacing * (bar_count + 1)) // bar_count
        )

        bar_count  = min(bar_count, len(spectrum))
        bar_values = aggregate_spectrum(spectrum, bar_count)
        bar_values = np.clip(bar_values * amplitude_scale, 0.0, 1.0)
        if response_curve > 0:
            bar_values = np.power(bar_values, response_curve)

        left_surface = Image.new("RGBA", (draw_width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(left_surface)

        for i, value in enumerate(bar_values):
            bar_h = max(1, int(value * self.height * 0.92))
            x0    = spacing + i * (bar_w + spacing)
            x1    = x0 + bar_w
            y0    = self.height - bar_h
            y1    = self.height

            if x0 >= draw_width:
                continue
            x1 = min(x1, draw_width - 1)

            if color_top != color_bot and bar_h > 2:
                grad = _gradient_column(bar_w, bar_h, color_top, color_bot)
                if corner_radius > 0 and bar_h > corner_radius * 2:
                    mask = Image.new("L", (bar_w, bar_h), 0)
                    ImageDraw.Draw(mask).rounded_rectangle(
                        [0, 0, bar_w - 1, bar_h - 1], corner_radius, fill=255
                    )
                    grad.putalpha(mask)
                left_surface.paste(grad, (x0, y0), grad)
            else:
                fill = color_top
                if corner_radius > 0 and bar_h > corner_radius * 2:
                    draw.rounded_rectangle([x0, y0, x1, y1], corner_radius, fill=fill)
                else:
                    draw.rectangle([x0, y0, x1, y1], fill=fill)

            if peak_on and bar_h > 4:
                draw.rectangle([x0, y0, x1, y0 + 2], fill=color_top)

        if mirror:
            right = left_surface.transpose(Image.FLIP_LEFT_RIGHT)
            surface.paste(left_surface, (0, 0))
            surface.paste(right, (draw_width, 0))
        else:
            surface = left_surface

        return surface
