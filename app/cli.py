from __future__ import annotations
import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from app.audio import analyze
from app.encoder import Encoder
from app.compositor import Compositor
from app.presets import build_project_from_quick_args, list_layer_presets, load_project_file
from app.layers.bars import BarsLayer
from app.layers.wavebars import WaveBarsLayer
from app.layers.waveform import WaveformLayer
from app.layers.circular import CircularLayer
from app.layers.pulse import PulseLayer
from app.layers.particles import ParticlesLayer
from app.layers.text import TextLayer
from app.layers.timer import TimerLayer
from app.layers.base import BaseLayer
from app.config import ProjectConfig, LayerConfig

app = typer.Typer(help="Audio visualizer video generator")
console = Console()

_BANNER = """\
 █████╗ ██╗   ██╗██████╗ ██╗ ██████╗
██╔══██╗██║   ██║██╔══██╗██║██╔═══██╗
███████║██║   ██║██║  ██║██║██║   ██║
██╔══██║██║   ██║██║  ██║██║██║   ██║
██║  ██║╚██████╔╝██████╔╝██║╚██████╔╝
╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝

███████╗██████╗ ███████╗ ██████╗████████╗██████╗
██╔════╝██╔══██╗██╔════╝██╔════╝╚══██╔══╝██╔══██╗
███████╗██████╔╝█████╗  ██║        ██║   ██████╔╝
╚════██║██╔═══╝ ██╔══╝  ██║        ██║   ██╔══██╗
███████║██║     ███████╗╚██████╗   ██║   ██║  ██║
╚══════╝╚═╝     ╚══════╝ ╚═════╝   ╚═╝   ╚═╝  ╚═╝"""


@app.callback()
def _banner(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is not None:
        from rich.console import Console as _C
        console.print()
        _C(width=200).print(_BANNER, style="bold cyan", markup=False, no_wrap=True)
        console.print("[dim]audio visualizer · mp3/wav/flac → mp4[/dim]")
        console.print()

LAYER_CLASSES: dict[str, type[BaseLayer]] = {
    "bars": BarsLayer,
    "wavebars": WaveBarsLayer,
    "waveform": WaveformLayer,
    "circular": CircularLayer,
    "pulse": PulseLayer,
    "particles": ParticlesLayer,
    "text": TextLayer,
    "timer": TimerLayer,
}


def build_layers(project: ProjectConfig) -> list[BaseLayer]:
    layers = []
    for layer_cfg in project.layers:
        cls = LAYER_CLASSES.get(layer_cfg.type)
        if cls is None:
            console.print(f"[yellow]Unknown layer type '{layer_cfg.type}', skipping[/yellow]")
            continue
        cfg_dict = {
            "type":       layer_cfg.type,
            **layer_cfg.model_extra,
            "x":          layer_cfg.x,
            "y":          layer_cfg.y,
            "width":      layer_cfg.width,
            "height":     layer_cfg.height,
            "opacity":    layer_cfg.opacity,
            "blend_mode": layer_cfg.blend_mode,
            # Serialize EffectConfig → dict so compositor can call .get() on it
            "effects":    layer_cfg.effects.model_dump(),
        }
        layers.append(cls(cfg_dict, project))
    return layers


def run_render(project: ProjectConfig, dump_frame: int | None = None) -> None:
    console.print(f"[cyan]Analyzing audio:[/cyan] {project.audio}")
    frames, sr = analyze(project.audio, project.fps)
    console.print(f"[cyan]{len(frames)} frames at {sr}Hz[/cyan]")

    layers = build_layers(project)
    comp   = Compositor(project, layers)

    if dump_frame is not None:
        idx = max(0, min(dump_frame, len(frames) - 1))
        bg  = comp._build_background()
        out = comp.composite_frame(frames[idx], bg)
        png_path = str(Path(project.output).with_name(Path(project.output).stem + f"_frame{idx}.png"))
        out.save(png_path)
        console.print(f"[green]Frame {idx} saved to {png_path}[/green]")
        return

    console.print(f"[cyan]Rendering {len(frames)} frames → {project.output}[/cyan]")
    with Encoder(project) as enc:
        comp.render(frames, enc)
        console.print("[cyan]Finalizing video encode...[/cyan]")
    console.print(f"[green]Done! Output: {project.output}[/green]")


@app.command("quick")
def quick(
    audio:      str            = typer.Option(...,  "--audio",      help="Input audio file"),
    output:     str            = typer.Option("output.mp4", "--output", help="Output MP4"),
    style:      str | None     = typer.Option(None, "--style",   help="bars|wavebars|waveform|circular|pulse|particles|text|timer"),
    preset:     str | None     = typer.Option(None, "--preset",  help="Preset name"),
    background: str | None     = typer.Option(None,  "--background", help="Background image path"),
    background_fit: str        = typer.Option("cover", "--background-fit", help="cover|contain|stretch|center"),
    background_color: str      = typer.Option("#000000", "--background-color", help="Background or padding color"),
    width:      int            = typer.Option(1920,  "--width"),
    height:     int            = typer.Option(1080,  "--height"),
    fps:        int            = typer.Option(30,    "--fps"),
    video_preset: str          = typer.Option("veryfast", "--video-preset", help="FFmpeg x264 preset"),
    crf:        int            = typer.Option(23, "--crf", help="x264 CRF quality: 0 lossless, 18 high, 23 default, 51 lowest"),
    bar_count:  int | None     = typer.Option(None,  "--bar-count"),
    amplitude_scale: float | None = typer.Option(None, "--amplitude-scale", help="Boost visualizer height/reactivity"),
    glow_scale: float | None = typer.Option(None, "--glow-scale", help="Internal glow render scale; lower is faster"),
    text_content: str | None = typer.Option(None, "--text-content", help="Text content for text style"),
    dump_frame: int | None     = typer.Option(None,  "--dump-frame", help="Render single frame to PNG"),
):
    overrides: dict = {}
    if bar_count is not None:
        overrides["bar_count"] = bar_count
    if amplitude_scale is not None:
        overrides["amplitude_scale"] = amplitude_scale
    if glow_scale is not None:
        overrides["effects"] = {"glow": True, "glow_scale": glow_scale}
    if text_content is not None:
        overrides["content"] = text_content

    project = build_project_from_quick_args(
        audio=audio, output=output, style=style, preset_name=preset,
        background=background, background_fit=background_fit, background_color=background_color,
        width=width, height=height, fps=fps, video_preset=video_preset, crf=crf,
        overrides=overrides,
    )
    run_render(project, dump_frame=dump_frame)


@app.command("presets")
def presets():
    table = Table("Preset", "Pattern")
    for preset in list_layer_presets():
        table.add_row(preset["name"], preset["pattern"])
    console.print(table)


@app.command("render")
def render(
    project_file: str          = typer.Argument(..., help="Path to project JSON file"),
    dump_frame:   int | None    = typer.Option(None, "--dump-frame"),
):
    project = load_project_file(project_file)
    run_render(project, dump_frame=dump_frame)


if __name__ == "__main__":
    app()
