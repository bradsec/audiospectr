from __future__ import annotations
from typing import TYPE_CHECKING
from PIL import Image, ImageFilter, ImageColor
import numpy as np
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from app.audio import FrameData
from app.config import ProjectConfig
from app.layers.base import BaseLayer
from app.effects import apply_glow, apply_grain, apply_blur

if TYPE_CHECKING:
    from app.encoder import Encoder


class Compositor:
    def __init__(self, project: ProjectConfig, layers: list[BaseLayer]) -> None:
        self._project = project
        self._layers  = layers
        self._bg_cache: Image.Image | None = None

    def _build_background(self) -> Image.Image:
        w, h = self._project.resolution
        bg_cfg = self._project.background

        if bg_cfg.type == "image" and bg_cfg.path:
            bg = _fit_background_image(
                Image.open(bg_cfg.path).convert("RGB"),
                (w, h),
                bg_cfg.fit,
                ImageColor.getrgb(bg_cfg.color),
            )
        else:
            color = ImageColor.getrgb(bg_cfg.color)
            bg = Image.new("RGB", (w, h), color)

        if bg_cfg.blur > 0:
            bg = bg.filter(ImageFilter.GaussianBlur(bg_cfg.blur))

        if bg_cfg.dim > 0:
            overlay = Image.new("RGB", (w, h), (0, 0, 0))
            bg = Image.blend(bg, overlay, bg_cfg.dim)

        return bg

    def _get_background(self, frame_data: FrameData) -> Image.Image:
        if self._bg_cache is None:
            self._bg_cache = self._build_background()

        bg_cfg = self._project.background
        if not bg_cfg.parallax:
            return self._bg_cache.copy()

        w, h = self._project.resolution
        progress = frame_data.frame_index / max(frame_data.total_frames - 1, 1)
        zoom = 1.0 + bg_cfg.parallax_speed * progress
        new_w = int(w / zoom)
        new_h = int(h / zoom)
        left  = (w - new_w) // 2
        top   = (h - new_h) // 2
        cropped = self._bg_cache.crop((left, top, left + new_w, top + new_h))
        return cropped.resize((w, h), Image.LANCZOS)

    def composite_frame(self, frame_data: FrameData, background: Image.Image) -> Image.Image:
        canvas = background.convert("RGBA")

        for layer in self._layers:
            surface = layer.render(frame_data)          # RGBA

            fx = layer.config.get("effects", {})
            if fx.get("glow"):
                surface = apply_glow(
                    surface,
                    intensity=float(fx.get("glow_intensity", 1.0)),
                    radius=int(fx.get("glow_radius", 15)),
                    scale=float(fx.get("glow_scale", 0.5)),
                )
            grain = float(fx.get("grain", 0))
            if grain > 0:
                surface = apply_grain(surface, grain)
            blur = float(fx.get("blur", 0))
            if blur > 0:
                surface = apply_blur(surface, blur)

            if layer.opacity < 1.0:
                arr = np.array(surface, dtype=np.float32)
                arr[:, :, 3] *= layer.opacity
                surface = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")

            if layer.blend_mode == "add":
                canvas = _blend_add(canvas, surface, (layer.x, layer.y))
            elif layer.blend_mode == "screen":
                canvas = _blend_screen(canvas, surface, (layer.x, layer.y))
            else:
                canvas.paste(surface, (layer.x, layer.y), surface)

        return canvas.convert("RGB")

    def render(self, frame_data_list: list[FrameData], encoder: "Encoder") -> None:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}/{task.total}"),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("Rendering", total=len(frame_data_list))
            for frame_data in frame_data_list:
                bg = self._get_background(frame_data)
                frame = self.composite_frame(frame_data, bg)
                encoder.write_frame(frame)
                progress.advance(task)


def _blend_add(canvas: Image.Image, surface: Image.Image, pos: tuple[int, int]) -> Image.Image:
    """Additive blend: paste surface onto canvas at pos using additive compositing."""
    w, h = surface.size
    cx, cy = pos
    cw, ch = canvas.size

    # Clamp source rect to canvas bounds (handles negative cx/cy)
    src_x = max(0, -cx)
    src_y = max(0, -cy)
    dst_x = max(0, cx)
    dst_y = max(0, cy)
    rw = min(w - src_x, cw - dst_x)
    rh = min(h - src_y, ch - dst_y)
    if rw <= 0 or rh <= 0:
        return canvas

    region = canvas.crop((dst_x, dst_y, dst_x + rw, dst_y + rh)).convert("RGBA")
    overlay = surface.crop((src_x, src_y, src_x + rw, src_y + rh)).convert("RGBA")

    # Load both images as (h, w, 4) arrays, operate on channel slices
    dst = np.array(region, dtype=np.float32)
    src = np.array(overlay, dtype=np.float32)
    alpha = src[:, :, 3:4] / 255.0

    # Additive blend: add color channels weighted by source alpha, expand destination alpha
    dst[:, :, :3] = np.clip(dst[:, :, :3] + src[:, :, :3] * alpha, 0, 255)
    dst[:, :, 3] = np.maximum(dst[:, :, 3], src[:, :, 3])

    blended = Image.fromarray(dst.astype(np.uint8), "RGBA")
    canvas.paste(blended, (dst_x, dst_y))
    return canvas


def _blend_screen(canvas: Image.Image, surface: Image.Image, pos: tuple[int, int]) -> Image.Image:
    """Screen blend source onto canvas at pos, weighted by source alpha."""
    w, h = surface.size
    cx, cy = pos
    cw, ch = canvas.size

    src_x = max(0, -cx)
    src_y = max(0, -cy)
    dst_x = max(0, cx)
    dst_y = max(0, cy)
    rw = min(w - src_x, cw - dst_x)
    rh = min(h - src_y, ch - dst_y)
    if rw <= 0 or rh <= 0:
        return canvas

    region = canvas.crop((dst_x, dst_y, dst_x + rw, dst_y + rh)).convert("RGBA")
    overlay = surface.crop((src_x, src_y, src_x + rw, src_y + rh)).convert("RGBA")

    dst = np.array(region, dtype=np.float32)
    src = np.array(overlay, dtype=np.float32)
    alpha = src[:, :, 3:4] / 255.0
    screened = 255.0 - ((255.0 - dst[:, :, :3]) * (255.0 - src[:, :, :3]) / 255.0)
    dst[:, :, :3] = np.clip(dst[:, :, :3] * (1.0 - alpha) + screened * alpha, 0, 255)
    dst[:, :, 3] = np.maximum(dst[:, :, 3], src[:, :, 3])

    blended = Image.fromarray(dst.astype(np.uint8), "RGBA")
    canvas.paste(blended, (dst_x, dst_y))
    return canvas


def _resize_cover(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    target_w, target_h = size
    scale = max(target_w / image.width, target_h / image.height)
    resized = image.resize(
        (max(1, int(round(image.width * scale))), max(1, int(round(image.height * scale)))),
        Image.LANCZOS,
    )
    left = max(0, (resized.width - target_w) // 2)
    top = max(0, (resized.height - target_h) // 2)
    return resized.crop((left, top, left + target_w, top + target_h))


def _fit_background_image(
    image: Image.Image,
    size: tuple[int, int],
    fit: str,
    pad_color: tuple[int, int, int],
) -> Image.Image:
    target_w, target_h = size

    if fit == "stretch":
        return image.resize(size, Image.LANCZOS)

    if fit == "cover":
        return _resize_cover(image, size)

    canvas = Image.new("RGB", size, pad_color)

    if fit == "contain":
        scale = min(target_w / image.width, target_h / image.height)
        fitted = image.resize(
            (
                max(1, int(round(image.width * scale))),
                max(1, int(round(image.height * scale))),
            ),
            Image.LANCZOS,
        )
    else:
        fitted = image

    left = (target_w - fitted.width) // 2
    top = (target_h - fitted.height) // 2

    src_left = max(0, -left)
    src_top = max(0, -top)
    dst_left = max(0, left)
    dst_top = max(0, top)
    paste_w = min(fitted.width - src_left, target_w - dst_left)
    paste_h = min(fitted.height - src_top, target_h - dst_top)
    if paste_w <= 0 or paste_h <= 0:
        return canvas

    crop = fitted.crop((src_left, src_top, src_left + paste_w, src_top + paste_h))
    canvas.paste(crop, (dst_left, dst_top))
    return canvas
