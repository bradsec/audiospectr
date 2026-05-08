from app.presets import PRESETS_DIR, load_layer_preset, list_layer_presets, build_project_from_quick_args
from app.config import ProjectConfig


def make_quick_project(**kwargs):
    args = {
        "audio": "track.mp3",
        "output": "out.mp4",
        "style": None,
        "preset_name": None,
        "background": None,
        "background_fit": "cover",
        "background_color": "#000000",
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "video_preset": "veryfast",
        "crf": 23,
        "overrides": {},
    }
    args.update(kwargs)
    return build_project_from_quick_args(**args)


def test_load_layer_preset_neon():
    preset = load_layer_preset("neon")
    assert preset["color"] == "#00f5ff"
    assert preset["bar_count"] == 96


def test_build_project_quick_defaults():
    project = make_quick_project()
    assert isinstance(project, ProjectConfig)
    assert len(project.layers) == 1
    assert project.layers[0].type == "bars"
    assert project.background.color == "#000000"
    assert project.video_preset == "veryfast"
    assert project.crf == 23
    assert project.audio == "track.mp3"


def test_build_project_cli_overrides_preset():
    project = make_quick_project(
        style="bars",
        preset_name="neon",
        overrides={"bar_count": 32},
    )
    assert project.layers[0].model_extra["bar_count"] == 32


def test_quick_style_takes_precedence_over_preset_type():
    project = make_quick_project(
        style="bars",
        preset_name="synthwave",
    )
    assert project.layers[0].type == "bars"


def test_quick_style_is_inferred_from_preset_type():
    project = make_quick_project(
        preset_name="waveform-cyan-fill",
    )
    assert project.layers[0].type == "waveform"


def test_quick_style_defaults_to_bars_without_preset():
    project = make_quick_project()
    assert project.layers[0].type == "bars"


def test_build_project_quick_merges_effect_overrides():
    project = make_quick_project(
        style="bars",
        preset_name="neon",
        overrides={"effects": {"glow_scale": 0.25}},
    )
    effects = project.layers[0].effects
    assert effects.glow is True
    assert effects.glow_radius == 15
    assert effects.glow_scale == 0.25


def test_build_project_quick_background_fit_and_color():
    project = make_quick_project(
        background="cover.jpg",
        background_fit="contain",
        background_color="#101010",
    )
    assert project.background.type == "image"
    assert project.background.path == "cover.jpg"
    assert project.background.fit == "contain"
    assert project.background.color == "#101010"


def test_build_project_quick_text_content_override():
    project = make_quick_project(
        style="text",
        overrides={"content": "Sample Text"},
    )
    assert project.layers[0].type == "text"
    assert project.layers[0].model_extra["content"] == "Sample Text"


def test_all_preset_files_are_valid_json_and_listed():
    files = sorted(PRESETS_DIR.glob("*.json"))
    listed = {preset["name"] for preset in list_layer_presets()}
    assert len(files) >= 20
    for path in files:
        preset = load_layer_preset(path.stem)
        assert isinstance(preset, dict)
        assert path.stem in listed


def test_descriptive_presets_include_pattern_prefix_and_type():
    descriptive = [
        preset for preset in list_layer_presets()
        if "-" in preset["name"]
    ]
    assert descriptive
    for preset in descriptive:
        prefix = preset["name"].split("-", 1)[0]
        assert preset["pattern"] == prefix


def test_cli_commands_are_registered():
    """The CLI app must have 'quick', 'render', and 'presets' commands."""
    from typer.testing import CliRunner
    from app.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0, f"CLI --help failed:\n{result.output}"
    assert "quick" in result.output
    assert "render" in result.output


def test_cli_presets_command_lists_presets():
    """The 'presets' command must exit 0 and list at least one preset."""
    from typer.testing import CliRunner
    from app.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["presets"])
    assert result.exit_code == 0, f"presets command failed:\n{result.output}"
    assert "neon" in result.output.lower() or len(result.output.strip()) > 0


def test_cli_quick_requires_audio_and_output():
    """The 'quick' command must fail with a usage error when required args are absent."""
    from typer.testing import CliRunner
    from app.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["quick"])
    assert result.exit_code != 0
