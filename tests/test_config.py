import pytest
from pydantic import ValidationError
from app.config import ProjectConfig, BackgroundConfig, LayerConfig, EffectConfig


def test_project_config_defaults():
    cfg = ProjectConfig(audio="track.mp3", output="out.mp4")
    assert cfg.resolution == (1920, 1080)
    assert cfg.fps == 30
    assert cfg.video_preset == "veryfast"
    assert cfg.crf == 23
    assert cfg.background.color == "#000000"
    assert cfg.background.fit == "cover"
    assert cfg.layers == []


def test_project_config_rejects_zero_fps():
    with pytest.raises(ValidationError):
        ProjectConfig(audio="track.mp3", output="out.mp4", fps=0)


def test_project_config_rejects_invalid_crf():
    with pytest.raises(ValidationError):
        ProjectConfig(audio="track.mp3", output="out.mp4", crf=52)


def test_layer_config_extra_fields_allowed():
    layer = LayerConfig(type="bars", bar_count=64)
    assert layer.type == "bars"
    assert layer.model_extra["bar_count"] == 64


def test_effect_config_defaults():
    fx = EffectConfig()
    assert fx.glow is False
    assert fx.glow_intensity == 1.0
    assert fx.glow_scale == 0.5
    assert fx.grain == 0.0
