#!/usr/bin/env python3
"""Generate background mode example images for the README.

Run from the project root:
    uv run python tools/gen_bg_examples.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from PIL import Image, ImageFilter, ImageColor

from app.audio import FrameData
from app.config import ProjectConfig, BackgroundConfig
from app.compositor import _fit_background_image
from app.effects import apply_glow
from app.layers.bars import BarsLayer
from app.layers.wavebars import WaveBarsLayer
from app.layers.waveform import WaveformLayer
from app.layers.circular import CircularLayer
from app.layers.pulse import PulseLayer
from app.layers.particles import ParticlesLayer
from app.layers.text import TextLayer
from app.layers.timer import TimerLayer

W, H = 960, 540
BG_169 = Path("testbackground169.png")
BG_11  = Path("testbackground11.png")
OUT_DIR = Path("docs/images/backgrounds")


def _make_spectrum(n: int = 1025) -> np.ndarray:
    x = np.linspace(0, 1, n)
    spec = 0.85 * np.exp(-9 * x) + 0.45 * np.exp(-30 * (x - 0.04) ** 2)
    spec += 0.25 * np.exp(-5 * (x - 0.15) ** 2)
    spec += 0.12 * np.sin(np.pi * x * 18) * np.exp(-5 * x)
    spec += 0.08 * (1 - x)
    return np.clip(spec, 0.0, 1.0).astype(np.float32)


def _make_waveform(n: int = 4410) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi * 3, n)
    wave = 0.55 * np.sin(t) + 0.22 * np.sin(2.5 * t) + 0.12 * np.sin(7 * t)
    return wave.astype(np.float32)


def _frame(index: int = 45, total: int = 90) -> FrameData:
    return FrameData(
        spectrum=_make_spectrum(),
        waveform=_make_waveform(),
        rms=0.72,
        bass=0.78,
        mid=0.44,
        high=0.18,
        sample_rate=44100,
        frame_index=index,
        total_frames=total,
    )


def _project(
    fit: str,
    bg_path: Path,
    *,
    blur: float = 0.0,
    dim: float = 0.0,
    color: str = "#000000",
) -> ProjectConfig:
    return ProjectConfig(
        resolution=(W, H),
        fps=30,
        audio="dummy.mp3",
        output="dummy.mp4",
        background=BackgroundConfig(
            type="image",
            path=str(bg_path),
            fit=fit,
            color=color,
            blur=blur,
            dim=dim,
        ),
        metadata={"title": "Track Title", "artist": "Artist Name"},
    )


def _build_bg(project: ProjectConfig) -> Image.Image:
    cfg = project.background
    bg = _fit_background_image(
        Image.open(cfg.path).convert("RGB"),
        project.resolution,
        cfg.fit,
        ImageColor.getrgb(cfg.color),
    )
    if cfg.blur > 0:
        bg = bg.filter(ImageFilter.GaussianBlur(cfg.blur))
    if cfg.dim > 0:
        overlay = Image.new("RGB", project.resolution, (0, 0, 0))
        bg = Image.blend(bg, overlay, cfg.dim)
    return bg


def _apply_fx(config: dict, surface: Image.Image) -> Image.Image:
    fx = config.get("effects", {})
    if fx.get("glow"):
        surface = apply_glow(
            surface,
            intensity=float(fx.get("glow_intensity", 1.0)),
            radius=int(fx.get("glow_radius", 15)),
            scale=float(fx.get("glow_scale", 0.5)),
        )
    return surface


def _composite(bg: Image.Image, surface: Image.Image, x: int = 0, y: int = 0) -> Image.Image:
    canvas = bg.convert("RGBA")
    canvas.paste(surface, (x, y), surface)
    return canvas.convert("RGB")


def _save(img: Image.Image, name: str) -> None:
    path = OUT_DIR / name
    img.save(str(path))
    print(f"  saved → {path}")


def _render(project: ProjectConfig, layer_cfg: dict, frame: FrameData) -> tuple[Image.Image, int, int]:
    cls = {
        "bars": BarsLayer,
        "wavebars": WaveBarsLayer,
        "waveform": WaveformLayer,
        "circular": CircularLayer,
        "pulse": PulseLayer,
        "particles": ParticlesLayer,
        "text": TextLayer,
        "timer": TimerLayer,
    }[layer_cfg["type"]]
    layer = cls(layer_cfg, project)
    surface = layer.render(frame)
    surface = _apply_fx(layer_cfg, surface)
    return surface, layer_cfg.get("x", 0), layer_cfg.get("y", 0)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frame = _frame()

    # ── 1. cover + 16:9 image + dim → bars ──────────────────────────────────
    print("1/8  bars — cover fit, 16:9 image, dim 0.3")
    proj = _project("cover", BG_169, dim=0.3)
    bg   = _build_bg(proj)
    layer_cfg = {
        "type": "bars", "x": 0, "y": H - 210, "width": W, "height": 210,
        "bar_count": 80, "color": "#00f5ff", "secondary_color": "#ff00cc",
        "mirror": True, "amplitude_scale": 3.5, "corner_radius": 4,
        "effects": {"glow": True, "glow_intensity": 1.4, "glow_radius": 14, "glow_scale": 0.5},
    }
    surf, lx, ly = _render(proj, layer_cfg, frame)
    _save(_composite(bg, surf, lx, ly), "bg-cover-16x9.png")

    # ── 2. cover + 1:1 image + dim → circular ───────────────────────────────
    print("2/8  circular — cover fit, 1:1 image, dim 0.3")
    proj = _project("cover", BG_11, dim=0.3)
    bg   = _build_bg(proj)
    layer_cfg = {
        "type": "circular", "x": 0, "y": 0, "width": W, "height": H,
        "bar_count": 88, "color": "#cc88ff", "bar_width": 5,
        "amplitude_scale": 4.5, "rotation_speed": 0.0,
        "smoothing_factor": 0.0,
        "effects": {"glow": True, "glow_intensity": 1.2, "glow_radius": 10, "glow_scale": 0.5},
    }
    surf, lx, ly = _render(proj, layer_cfg, frame)
    _save(_composite(bg, surf, lx, ly), "bg-cover-1x1.png")

    # ── 3. contain + 1:1 image + black padding → waveform ───────────────────
    print("3/8  waveform — contain fit, 1:1 image, black padding")
    proj = _project("contain", BG_11, color="#0a0a0a")
    bg   = _build_bg(proj)
    layer_cfg = {
        "type": "waveform", "x": 0, "y": H // 2 - 90, "width": W, "height": 180,
        "color": "#ffffff", "line_width": 4, "fill_color": "#4466ff",
        "smoothing_factor": 0.0,
    }
    surf, lx, ly = _render(proj, layer_cfg, frame)
    _save(_composite(bg, surf, lx, ly), "bg-contain-1x1.png")

    # ── 4. stretch + 1:1 image + dim → wavebars ─────────────────────────────
    print("4/8  wavebars — stretch fit, 1:1 image, dim 0.2")
    proj = _project("stretch", BG_11, dim=0.2)
    bg   = _build_bg(proj)
    layer_cfg = {
        "type": "wavebars", "x": 0, "y": 0, "width": W, "height": H,
        "bar_count": 80, "color": "#44ee88",
        "amplitude_scale": 3.2, "height_ratio": 0.42,
        "smoothing_factor": 0.0,
    }
    surf, lx, ly = _render(proj, layer_cfg, frame)
    _save(_composite(bg, surf, lx, ly), "bg-stretch.png")

    # ── 5. center + 1:1 image + dark padding → pulse ────────────────────────
    print("5/8  pulse — center fit, 1:1 image, dark padding")
    proj = _project("center", BG_11, color="#070710")
    bg   = _build_bg(proj)
    layer_cfg = {
        "type": "pulse", "x": 0, "y": 0, "width": W, "height": H,
        "color": "#00f5ff", "base_radius": 130, "ring_count": 4,
        "spoke_count": 24, "spoke_length": 0.22,
        "ring_width": 5, "max_scale": 1.45,
        "effects": {"glow": True, "glow_intensity": 1.3, "glow_radius": 12, "glow_scale": 0.5},
    }
    surf, lx, ly = _render(proj, layer_cfg, frame)
    _save(_composite(bg, surf, lx, ly), "bg-center.png")

    # ── 6. cover + 16:9 + blur → particles (pre-warmed) ─────────────────────
    print("6/8  particles — cover fit, 16:9 image, blur 8")
    proj = _project("cover", BG_169, blur=8.0)
    bg   = _build_bg(proj)
    layer_cfg = {
        "type": "particles", "x": 0, "y": 0, "width": W, "height": H,
        "flow_mode": "directional", "direction": 270,
        "spawn_rate": 24, "velocity_multiplier": 5.5,
        "particle_size": 4, "color": "#ff8822",
        "lifetime": 80, "max_particles": 1400,
        "spawn_spread": 0.5,
    }
    from app.layers.particles import ParticlesLayer as PL
    p_layer = PL(layer_cfg, proj)
    for i in range(65):
        p_layer.render(_frame(i, 90))
    surf = p_layer.render(_frame(45, 90))
    _save(_composite(bg, surf), "bg-blur.png")

    # ── 7. cover + 16:9 + dim → text ────────────────────────────────────────
    print("7/8  text — cover fit, 16:9 image, dim 0.6")
    proj = _project("cover", BG_169, dim=0.6)
    bg   = _build_bg(proj)
    layer_cfg = {
        "type": "text", "x": 80, "y": 160, "width": W - 160, "height": 220,
        "content": "{artist}\n{title}",
        "font_size": 64, "color": "#ffffff", "alignment": "left",
    }
    surf, lx, ly = _render(proj, layer_cfg, frame)
    _save(_composite(bg, surf, lx, ly), "bg-dim.png")

    # ── 8. cover + 1:1 + blur + dim → timer ─────────────────────────────────
    print("8/8  timer — cover fit, 1:1 image, blur 6 + dim 0.45")
    proj = _project("cover", BG_11, blur=6.0, dim=0.45)
    bg   = _build_bg(proj)
    layer_cfg = {
        "type": "timer", "x": 0, "y": H - 20, "width": W, "height": 20,
        "color": "#00f5ff", "background_color": "#111111",
        "corner_radius": 0,
    }
    surf, lx, ly = _render(proj, layer_cfg, frame)
    _save(_composite(bg, surf, lx, ly), "bg-blur-dim.png")

    print(f"\nDone — {len(list(OUT_DIR.glob('*.png')))} images in {OUT_DIR}/")


if __name__ == "__main__":
    main()
