from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, field_validator


class EffectConfig(BaseModel):
    glow: bool = False
    glow_intensity: float = 1.0
    glow_radius: int = 15
    glow_scale: float = 0.5
    grain: float = 0.0
    blur: float = 0.0


class BackgroundConfig(BaseModel):
    type: Literal["color", "image"] = "color"
    path: Optional[str] = None
    color: str = "#000000"
    fit: Literal["cover", "contain", "stretch", "center"] = "cover"
    blur: float = 0.0
    dim: float = 0.0
    parallax: bool = False
    parallax_speed: float = 0.02


class LayerConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: str
    x: int = 0
    y: int = 0
    width: Optional[int] = None
    height: Optional[int] = None
    opacity: float = 1.0
    blend_mode: Literal["normal", "add", "screen"] = "normal"
    effects: EffectConfig = EffectConfig()


class ProjectConfig(BaseModel):
    resolution: tuple[int, int] = (1920, 1080)
    fps: int = 30
    video_preset: str = "veryfast"
    crf: int = 23
    audio: str
    output: str = "output.mp4"
    background: BackgroundConfig = BackgroundConfig()
    layers: list[LayerConfig] = []
    metadata: dict[str, str] = {}

    @field_validator("fps")
    @classmethod
    def fps_must_be_positive(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("fps must be positive")
        return v

    @field_validator("crf")
    @classmethod
    def crf_must_be_valid(cls, v: int) -> int:
        if not 0 <= v <= 51:
            raise ValueError("crf must be between 0 and 51")
        return v
