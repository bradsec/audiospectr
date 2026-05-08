from __future__ import annotations
import json
from pathlib import Path
from app.config import ProjectConfig, LayerConfig, BackgroundConfig

PRESETS_DIR = Path(__file__).parent.parent / "presets"


def load_layer_preset(name: str) -> dict:
    path = PRESETS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Preset '{name}' not found at {path}")
    return json.loads(path.read_text())


def list_layer_presets() -> list[dict[str, str]]:
    presets: list[dict[str, str]] = []
    for path in sorted(PRESETS_DIR.glob("*.json")):
        data = json.loads(path.read_text())
        pattern = str(data.get("type") or path.stem.split("-", 1)[0])
        presets.append({
            "name": path.stem,
            "pattern": pattern,
            "file": path.name,
        })
    return presets


def load_project_file(path: str) -> ProjectConfig:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Project file not found: {path}")
    try:
        data = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in project file '{path}': {e}") from e
    return ProjectConfig.model_validate(data)


def build_project_from_quick_args(
    audio: str,
    output: str,
    style: str | None,
    preset_name: str | None,
    background: str | None,
    background_fit: str,
    background_color: str,
    width: int,
    height: int,
    fps: int,
    video_preset: str,
    crf: int,
    overrides: dict,
) -> ProjectConfig:
    layer_cfg: dict = {"width": width, "height": height}
    overrides = dict(overrides)

    if preset_name:
        preset = load_layer_preset(preset_name)
        layer_cfg.update(preset)

    layer_cfg["type"] = style or layer_cfg.get("type") or "bars"
    effect_overrides = overrides.pop("effects", None)
    layer_cfg.update(overrides)
    if effect_overrides:
        effects = dict(layer_cfg.get("effects", {}))
        effects.update(effect_overrides)
        layer_cfg["effects"] = effects

    bg = BackgroundConfig(color=background_color)
    if background:
        bg = BackgroundConfig(type="image", path=background, fit=background_fit, color=background_color)

    return ProjectConfig(
        resolution=(width, height),
        fps=fps,
        video_preset=video_preset,
        crf=crf,
        audio=audio,
        output=output,
        background=bg,
        layers=[LayerConfig.model_validate(layer_cfg)],
    )
