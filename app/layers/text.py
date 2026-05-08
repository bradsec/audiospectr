from __future__ import annotations
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageColor
from app.layers.base import BaseLayer
from app.audio import FrameData
from app.config import ProjectConfig


_FONT_LOAD_FAILED = object()


def _load_fallback_font(size: int) -> ImageFont.ImageFont:
    if sys.platform == "win32":
        windir = os.environ.get("WINDIR", "C:\\Windows")
        candidates = [
            os.path.join(windir, "Fonts", "arial.ttf"),
            os.path.join(windir, "Fonts", "segoeui.ttf"),
            os.path.join(windir, "Fonts", "calibri.ttf"),
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/SFNS.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default(size=size)


class TextLayer(BaseLayer):
    def __init__(self, config: dict, project: ProjectConfig) -> None:
        super().__init__(config, project)
        self._project = project
        self._font: object = None  # None = not tried, _FONT_LOAD_FAILED = failed, else FreeTypeFont

    def _get_font(self) -> ImageFont.ImageFont:
        font_path = self.config.get("font_path")
        font_size = int(self.config.get("font_size", 48))
        if font_path and self._font is None:
            try:
                self._font = ImageFont.truetype(font_path, font_size)
            except Exception:
                self._font = _FONT_LOAD_FAILED
        if isinstance(self._font, ImageFont.FreeTypeFont):
            return self._font
        return _load_fallback_font(font_size)

    def _resolve_content(self, content: str, frame_data: FrameData) -> str:
        meta = self._project.metadata
        fps  = self._project.fps
        elapsed = (frame_data.frame_index + 1) / max(fps, 1)
        minutes = int(elapsed) // 60
        seconds = int(elapsed) % 60
        return (
            content
            .replace("{title}",  meta.get("title",  ""))
            .replace("{artist}", meta.get("artist", ""))
            .replace("{time}",   f"{minutes}:{seconds:02d}")
        )

    def render(self, frame_data: FrameData) -> Image.Image:
        surface = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(surface)

        content   = self._resolve_content(self.config.get("content", ""), frame_data)
        color     = self.config.get("color", "#ffffff")
        alignment = self.config.get("alignment", "left")
        font      = self._get_font()
        r, g, b   = ImageColor.getrgb(color)

        bbox = draw.textbbox((0, 0), content, font=font)
        tw   = bbox[2] - bbox[0]
        th   = bbox[3] - bbox[1]

        if alignment == "center":
            x = (self.width - tw) // 2
        elif alignment == "right":
            x = self.width - tw - 10
        else:
            x = int(self.config.get("padding", 10))

        y = (self.height - th) // 2

        draw.text((x, y), content, font=font, fill=(r, g, b, 255))
        return surface
