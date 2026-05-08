from __future__ import annotations
from PIL import Image, ImageDraw, ImageColor
from app.layers.base import BaseLayer
from app.audio import FrameData
from app.config import ProjectConfig


class TimerLayer(BaseLayer):
    def render(self, frame_data: FrameData) -> Image.Image:
        surface = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(surface)

        style   = self.config.get("style", "bar")
        color   = self.config.get("color", "#ffffff")
        bg_col  = self.config.get("background_color")
        radius  = int(self.config.get("corner_radius", 0))

        progress = frame_data.frame_index / max(frame_data.total_frames - 1, 1)
        filled_w = max(1, int(self.width * progress))

        r, g, b = ImageColor.getrgb(color)

        if bg_col:
            rb, gb, bb = ImageColor.getrgb(bg_col)
            if radius > 0:
                draw.rounded_rectangle([0, 0, self.width - 1, self.height - 1],
                                        radius, fill=(rb, gb, bb, 180))
            else:
                draw.rectangle([0, 0, self.width - 1, self.height - 1],
                                fill=(rb, gb, bb, 180))

        if style == "bar":
            if radius > 0 and filled_w > radius * 2:
                draw.rounded_rectangle([0, 0, filled_w, self.height - 1],
                                        radius, fill=(r, g, b, 255))
            else:
                draw.rectangle([0, 0, filled_w, self.height - 1],
                                fill=(r, g, b, 255))
        else:  # "line" — point indicator
            x = min(int(self.width * progress), self.width - 1)
            draw.line([(x, 0), (x, self.height - 1)], fill=(r, g, b, 255), width=3)

        return surface
