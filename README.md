# audiospectr

`audiospectr` is a Python CLI application that turns audio files into animated MP4 videos with audio-reactive visualiser layers. It pre-analyses the audio into per-frame FFT, waveform, RMS, and frequency-band data, composites one or more RGBA layers over a colour or image background, then streams raw frames directly to FFmpeg for encoding.

## Features

- Input audio analysis for MP3, WAV, FLAC, M4A, and OGG files through `librosa`.
- MP4 export through system FFmpeg using H.264 video and AAC audio.
- Quick single-layer rendering from CLI flags.
- JSON project rendering for multi-layer compositions.
- Background colour or cover-cropped background image support, with blur, dimming, and optional parallax.
- Visualiser layers: `bars`, `wavebars`, `waveform`, `circular`, `pulse`, `particles`, `text`, and `timer`.
- Layer effects: glow, blur, grain, opacity, normal/add/screen blending.
- Built-in presets with descriptive pattern names, such as `bars-neon-mirror`, `waveform-cyan-fill`, and `circular-synthwave-orbit`.
- `--dump-frame` mode for rendering one preview PNG without encoding a full video.

## Visualiser Styles

| | |
|:---:|:---:|
| ![bars](docs/images/style-bars.png)<br>**bars** — frequency spectrum as vertical bars | ![wavebars](docs/images/style-wavebars.png)<br>**wavebars** — symmetric seewav-style bars |
| ![waveform](docs/images/style-waveform.png)<br>**waveform** — smoothed amplitude line | ![circular](docs/images/style-circular.png)<br>**circular** — radial bars around a ring |
| ![pulse](docs/images/style-pulse.png)<br>**pulse** — bass-reactive concentric rings | ![particles](docs/images/style-particles.png)<br>**particles** — audio-spawned floating dots |
| ![text](docs/images/style-text.png)<br>**text** — title, artist, or static label overlay | ![timer](docs/images/style-timer.png)<br>**timer** — playback progress bar or line |

## Preset Gallery

### Bars

| | | |
|:---:|:---:|:---:|
| ![bars-neon-mirror](docs/images/presets/bars-neon-mirror.png)<br>`bars-neon-mirror` | ![bars-cyberpunk-peaks](docs/images/presets/bars-cyberpunk-peaks.png)<br>`bars-cyberpunk-peaks` | ![bars-vaporwave-dream](docs/images/presets/bars-vaporwave-dream.png)<br>`bars-vaporwave-dream` |
| ![bars-ember-wide](docs/images/presets/bars-ember-wide.png)<br>`bars-ember-wide` | ![bars-bass-wall](docs/images/presets/bars-bass-wall.png)<br>`bars-bass-wall` | ![bars-ice-peaks](docs/images/presets/bars-ice-peaks.png)<br>`bars-ice-peaks` |
| ![bars-lofi-amber](docs/images/presets/bars-lofi-amber.png)<br>`bars-lofi-amber` | ![bars-minimal-white](docs/images/presets/bars-minimal-white.png)<br>`bars-minimal-white` | ![bars-noir-steel](docs/images/presets/bars-noir-steel.png)<br>`bars-noir-steel` |

### Wavebars

| | | |
|:---:|:---:|:---:|
| ![wavebars-seewav-classic](docs/images/presets/wavebars-seewav-classic.png)<br>`wavebars-seewav-classic` | ![wavebars-seewav-green](docs/images/presets/wavebars-seewav-green.png)<br>`wavebars-seewav-green` | ![wavebars-lofi-warm](docs/images/presets/wavebars-lofi-warm.png)<br>`wavebars-lofi-warm` |

### Waveform

| | | |
|:---:|:---:|:---:|
| ![waveform-magenta-glow](docs/images/presets/waveform-magenta-glow.png)<br>`waveform-magenta-glow` | ![waveform-cyan-fill](docs/images/presets/waveform-cyan-fill.png)<br>`waveform-cyan-fill` | ![waveform-dark-ember](docs/images/presets/waveform-dark-ember.png)<br>`waveform-dark-ember` |
| ![waveform-forest-line](docs/images/presets/waveform-forest-line.png)<br>`waveform-forest-line` | ![waveform-silk-line](docs/images/presets/waveform-silk-line.png)<br>`waveform-silk-line` | |

### Circular

| | | |
|:---:|:---:|:---:|
| ![circular-synthwave-orbit](docs/images/presets/circular-synthwave-orbit.png)<br>`circular-synthwave-orbit` | ![circular-vaporwave-halo](docs/images/presets/circular-vaporwave-halo.png)<br>`circular-vaporwave-halo` | ![circular-ice-ring](docs/images/presets/circular-ice-ring.png)<br>`circular-ice-ring` |
| ![circular-solar-ring](docs/images/presets/circular-solar-ring.png)<br>`circular-solar-ring` | | |

### Pulse

| | | |
|:---:|:---:|:---:|
| ![pulse-bass-ring](docs/images/presets/pulse-bass-ring.png)<br>`pulse-bass-ring` | ![pulse-hot-pink](docs/images/presets/pulse-hot-pink.png)<br>`pulse-hot-pink` | ![pulse-deep-blue](docs/images/presets/pulse-deep-blue.png)<br>`pulse-deep-blue` |
| ![pulse-spoked-electric](docs/images/presets/pulse-spoked-electric.png)<br>`pulse-spoked-electric` | | |

### Particles

| | | |
|:---:|:---:|:---:|
| ![particles-embers-rise](docs/images/presets/particles-embers-rise.png)<br>`particles-embers-rise` | ![particles-radial-sparks](docs/images/presets/particles-radial-sparks.png)<br>`particles-radial-sparks` | ![particles-updraft-stars](docs/images/presets/particles-updraft-stars.png)<br>`particles-updraft-stars` |
| ![particles-sidewind-cyan](docs/images/presets/particles-sidewind-cyan.png)<br>`particles-sidewind-cyan` | | |

### Timer

| | |
|:---:|:---:|
| ![timer-neon-bar](docs/images/presets/timer-neon-bar.png)<br>`timer-neon-bar` | ![timer-minimal-line](docs/images/presets/timer-minimal-line.png)<br>`timer-minimal-line` |

### Legacy

| | | | |
|:---:|:---:|:---:|:---:|
| ![neon](docs/images/presets/neon.png)<br>`neon` | ![minimal](docs/images/presets/minimal.png)<br>`minimal` | ![cyberpunk](docs/images/presets/cyberpunk.png)<br>`cyberpunk` | ![synthwave](docs/images/presets/synthwave.png)<br>`synthwave` |

## Background Image Modes

The `background` block in a project file (or `--background-fit` / `--background-color` flags in quick mode) controls how images are positioned and processed before layers are composited on top.

### Fit

| | |
|:---:|:---:|
| ![cover with 16:9 image](docs/images/backgrounds/bg-cover-16x9.png)<br>**`cover`** — 16:9 image, bars visualiser | ![cover with 1:1 image](docs/images/backgrounds/bg-cover-1x1.png)<br>**`cover`** — 1:1 image cropped to fill, circular visualiser |
| ![contain with 1:1 image](docs/images/backgrounds/bg-contain-1x1.png)<br>**`contain`** — 1:1 image letterboxed with black padding, waveform visualiser | ![stretch with 1:1 image](docs/images/backgrounds/bg-stretch.png)<br>**`stretch`** — 1:1 image distorted to fill, wavebars visualiser |
| ![center with 1:1 image](docs/images/backgrounds/bg-center.png)<br>**`center`** — 1:1 image at original size, pulse visualiser | |

- **`cover`** — scales to fill the frame, cropping the longer dimension. Best for wide backgrounds and blurred album art.
- **`contain`** — fits the whole image inside the frame, padding the remaining area with `color`. Best for square album covers you want to display in full.
- **`stretch`** — ignores aspect ratio and forces the image to exactly match the frame size.
- **`center`** — places the image at its native pixel size centred on the frame. If the image is smaller than the frame, `color` fills the edges; if larger, it is cropped to centre.

### Blur and dim

| | | |
|:---:|:---:|:---:|
| ![blur](docs/images/backgrounds/bg-blur.png)<br>**`blur: 8`** — particles visualiser | ![dim](docs/images/backgrounds/bg-dim.png)<br>**`dim: 0.6`** — text visualiser | ![blur + dim](docs/images/backgrounds/bg-blur-dim.png)<br>**`blur: 6, dim: 0.45`** — timer visualiser |

`blur` applies a Gaussian blur (value is the radius in pixels). `dim` blends the image toward black — `0.0` leaves the image unchanged, `1.0` produces solid black. Combine both to soften and darken a background so visualiser layers and text read clearly on top.

### Config examples

Square album cover centred with black letterbox:

```json
{
  "background": {
    "type": "image",
    "path": "cover.jpg",
    "fit": "contain",
    "color": "#000000"
  }
}
```

Full-screen cover image blurred and dimmed (typical album-art treatment):

```json
{
  "background": {
    "type": "image",
    "path": "cover.jpg",
    "fit": "cover",
    "blur": 6,
    "dim": 0.45
  }
}
```

Soft atmospheric background with parallax drift:

```json
{
  "background": {
    "type": "image",
    "path": "background.jpg",
    "fit": "cover",
    "blur": 10,
    "dim": 0.3,
    "parallax": true,
    "parallax_speed": 0.03
  }
}
```

## Requirements

- Python 3.11 or newer
- `uv` (package manager)
- FFmpeg available on `PATH`

On Debian or Ubuntu:

```bash
sudo apt update
sudo apt install ffmpeg python3 python3-venv
```

On macOS (Homebrew):

```bash
brew install ffmpeg
```

On Windows, download a build from [ffmpeg.org/download.html](https://ffmpeg.org/download.html), extract it, and add the `bin` folder to your `PATH` environment variable. Verify with `ffmpeg -version` in a new terminal.

## Setup

Install [uv](https://docs.astral.sh/uv/) if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install project dependencies:

```bash
uv sync --group dev
```

`uv` creates and manages the virtual environment automatically — no need to activate it. Prefix any command with `uv run` to use the project environment, or install globally with `uv tool install .` to use `spectr` directly.

Run the test suite:

```bash
uv run pytest
```

## Quick Render

The simplest render — one command, no background needed:

```bash
spectr quick --audio track.mp3 --preset bars-neon-mirror --output out.mp4
```

Add a cover image:

```bash
spectr quick \
  --audio track.mp3 \
  --background cover.jpg \
  --preset bars-neon-mirror \
  --output out.mp4
```

Preview a frame before committing to a full render — no FFmpeg, instant:

```bash
spectr quick \
  --audio track.mp3 \
  --background cover.jpg \
  --preset bars-neon-mirror \
  --output out.mp4 \
  --dump-frame 100
```

This writes `out.png` next to the output path and exits without encoding.

For full control over a single visualiser layer:

Useful options:

```text
--style bars|wavebars|waveform|circular|pulse|particles|text|timer
--preset bars-neon-mirror
--width 1920
--height 1080
--fps 30
--video-preset veryfast
--crf 23
--bar-count 96
--amplitude-scale 3.5
--glow-scale 0.5
--background-fit cover|contain|stretch|center
--background-color "#000000"
--dump-frame 150
```

`--dump-frame N` writes a PNG next to the configured output file and exits before FFmpeg encoding.

For faster renders, lower the output size or FPS, lower `--glow-scale`, or use a faster FFmpeg preset such as `--video-preset ultrafast`. For more reactive bars, increase `--amplitude-scale`.

CRF controls H.264 quality and size: lower values mean higher quality and larger files. Useful values are `18` for high quality, `20-23` for normal output, and `28` for smaller files.

If `--style` is omitted, quick mode uses the preset's `type`. If both are provided, `--style` wins.

If no preset is selected, quick mode renders the selected style in white over the default black background.

Background image fit modes:

- `cover`: fill the whole video while preserving aspect ratio, cropping edges if needed. Best for full-screen backgrounds.
- `contain`: fit the whole image inside the video while preserving aspect ratio, with padding around it. Best for square album art.
- `stretch`: force the image to exactly match the video size.
- `center`: place the image at original size in the centre, with padding or cropping if needed.

Square album cover centered with black padding:

```bash
spectr quick \
  --audio track.mp3 \
  --background cover.jpg \
  --background-fit contain \
  --background-color "#000000" \
  --style circular \
  --output album-cover.mp4
```

Full-screen image background:

```bash
spectr quick \
  --audio track.mp3 \
  --background wide-background.jpg \
  --background-fit cover \
  --preset bars-neon-mirror \
  --output fullscreen.mp4
```

List installed presets:

```bash
spectr presets
```

Preset names are pattern-first:

```text
bars-neon-mirror
bars-cyberpunk-peaks
bars-minimal-white
bars-bass-wall
bars-ember-wide
bars-ice-peaks
bars-lofi-amber
bars-vaporwave-dream
bars-noir-steel
waveform-silk-line
waveform-cyan-fill
waveform-magenta-glow
waveform-dark-ember
waveform-forest-line
wavebars-seewav-classic
wavebars-seewav-green
wavebars-lofi-warm
circular-synthwave-orbit
circular-ice-ring
circular-solar-ring
circular-vaporwave-halo
pulse-bass-ring
pulse-hot-pink
pulse-deep-blue
pulse-spoked-electric
particles-radial-sparks
particles-updraft-stars
particles-sidewind-cyan
particles-embers-rise
timer-neon-bar
timer-minimal-line
```

Legacy presets `neon`, `minimal`, `cyberpunk`, and `synthwave` are still available.

## JSON Project Render

Use `render` mode for multi-layer videos:

```bash
spectr render sample_project.json
```

Preview a single frame:

```bash
spectr render sample_project.json --dump-frame 150
```

Example project:

```json
{
  "resolution": [1920, 1080],
  "fps": 30,
  "audio": "track.mp3",
  "output": "out.mp4",
  "background": {
    "type": "image",
    "path": "cover.jpg",
    "fit": "cover",
    "color": "#000000",
    "blur": 4,
    "dim": 0.35
  },
  "metadata": {
    "title": "Song Title",
    "artist": "Artist Name"
  },
  "layers": [
    {
      "type": "bars",
      "x": 0,
      "y": 760,
      "width": 1920,
      "height": 300,
      "bar_count": 96,
      "color": "#00f5ff",
      "secondary_color": "#ff00cc",
      "mirror": true,
      "effects": {
        "glow": true,
        "glow_intensity": 1.5,
        "glow_radius": 15
      }
    },
    {
      "type": "text",
      "x": 80,
      "y": 60,
      "width": 1760,
      "height": 90,
      "content": "{artist} - {title}",
      "font_size": 52,
      "color": "#ffffff"
    },
    {
      "type": "timer",
      "x": 0,
      "y": 1065,
      "width": 1920,
      "height": 15,
      "color": "#00f5ff",
      "background_color": "#111111"
    }
  ]
}
```

## Examples

The `examples/` directory contains ready-to-run project files. Edit the `audio` and `output` paths in each file to point to your files, then run with `render`.

### Podcast episode — `examples/podcast.json`

Clean waveform with show name, episode title, and a progress bar — white on dark, no image needed.

```bash
spectr render examples/podcast.json
```

```json
{
  "resolution": [1920, 1080],
  "fps": 30,
  "audio": "episode.mp3",
  "output": "podcast.mp4",
  "background": {"type": "color", "color": "#0a0a0a"},
  "metadata": {"title": "Episode 42", "artist": "My Podcast"},
  "layers": [
    {
      "type": "waveform",
      "x": 0, "y": 380,
      "width": 1920, "height": 320,
      "color": "#ffffff",
      "line_width": 3
    },
    {
      "type": "text",
      "x": 80, "y": 80,
      "width": 1760, "height": 80,
      "content": "{artist}  ·  {title}",
      "font_size": 44,
      "color": "#cccccc"
    },
    {
      "type": "timer",
      "x": 0, "y": 1062,
      "width": 1920, "height": 18,
      "style": "bar",
      "color": "#ffffff",
      "background_color": "#222222"
    }
  ]
}
```

### Album / track share — `examples/album-single.json`

Bars over a blurred cover image, with artist name, track title, and a neon progress bar.

```bash
spectr render examples/album-single.json
```

```json
{
  "resolution": [1920, 1080],
  "fps": 30,
  "audio": "track.mp3",
  "output": "album-single.mp4",
  "background": {
    "type": "image",
    "path": "cover.jpg",
    "fit": "cover",
    "blur": 6,
    "dim": 0.45
  },
  "metadata": {"title": "Track Name", "artist": "Artist Name"},
  "layers": [
    {
      "type": "bars",
      "x": 0, "y": 700,
      "width": 1920, "height": 340,
      "bar_count": 96,
      "color": "#00f5ff",
      "secondary_color": "#ff00cc",
      "mirror": true,
      "effects": {
        "glow": true,
        "glow_intensity": 1.5,
        "glow_radius": 15
      }
    },
    {
      "type": "text",
      "x": 80, "y": 60,
      "width": 1760, "height": 80,
      "content": "{artist} — {title}",
      "font_size": 48,
      "color": "#ffffff"
    },
    {
      "type": "timer",
      "x": 0, "y": 1062,
      "width": 1920, "height": 18,
      "color": "#00f5ff",
      "background_color": "#111111"
    }
  ]
}
```

### Lofi / ambient session — `examples/lofi-ambient.json`

Warm circular ring with rising ember particles over a dimmed background — no text, pure motion.

```bash
spectr render examples/lofi-ambient.json
```

```json
{
  "resolution": [1920, 1080],
  "fps": 30,
  "audio": "session.mp3",
  "output": "lofi-ambient.mp4",
  "background": {
    "type": "image",
    "path": "background.jpg",
    "fit": "cover",
    "blur": 8,
    "dim": 0.6
  },
  "layers": [
    {
      "type": "circular",
      "x": 610, "y": 190,
      "width": 700, "height": 700,
      "bar_count": 72,
      "color": "#e8a040",
      "bar_width": 5,
      "rotation_speed": 0.2,
      "smoothing_factor": 0.88,
      "amplitude_scale": 4.5,
      "effects": {
        "glow": true,
        "glow_intensity": 1.3,
        "glow_radius": 14
      }
    },
    {
      "type": "particles",
      "x": 0, "y": 0,
      "width": 1920, "height": 1080,
      "flow_mode": "directional",
      "direction": 270,
      "spawn_rate": 18,
      "velocity_multiplier": 4.0,
      "particle_size": 3,
      "color": "#ff6600",
      "lifetime": 110,
      "max_particles": 2800,
      "effects": {
        "glow": true,
        "glow_intensity": 1.25,
        "glow_radius": 10
      }
    }
  ]
}
```

### Square post (Instagram / YouTube Short)

Centre the album cover with black padding, circular visualiser spinning around it:

```bash
spectr quick \
  --audio track.mp3 \
  --background cover.jpg \
  --background-fit contain \
  --background-color "#000000" \
  --preset circular-synthwave-orbit \
  --width 1080 --height 1080 \
  --output square.mp4
```

## Layer Configuration

All layers support common positioning and compositing fields:

```json
{
  "type": "bars",
  "x": 0,
  "y": 0,
  "width": 1920,
  "height": 1080,
    "opacity": 1.0,
    "blend_mode": "normal",
    "effects": {
      "glow": false,
      "glow_intensity": 1.0,
      "glow_radius": 15,
      "glow_scale": 0.5,
      "grain": 0.0,
      "blur": 0.0
    }
}
```

Supported `blend_mode` values are `normal`, `add`, and `screen`.

Visualiser-specific fields include:

- `bars`: `bar_count`, `bar_width`, `spacing`, `corner_radius`, `mirror`, `color`, `secondary_color`, `peak_indicators`, `smoothing_type`, `smoothing_factor`, `analyzer_range`, `amplitude_scale`, `response_curve`
- `wavebars`: `bar_count`, `bar_width`, `spacing_ratio`, `corner_radius`, `color`, `amplitude_scale`, `response_curve`, `reflection_alpha`, `height_ratio`, `smoothing_factor`
- `waveform`: `line_width`, `color`, `fill_color`, `smoothing_factor` (0.0–1.0, default 0.65 — higher values produce a slower, more fluid line)
- `circular`: `bar_count`, `radius`, `inner_radius`, `bar_width`, `rotation_speed`, `center_image`, `color`, `amplitude_scale`, `response_curve`, `min_bar_length`
- `pulse`: `base_radius`, `max_scale`, `ring_width`, `ring_count`, `spoke_count`, `spoke_length`, `spoke_width`, `core`, `core_scale`, `rotation_speed`, `color`, `glow_intensity`
- `particles`: `flow_mode`, `spawn_rate`, `velocity_multiplier`, `particle_size`, `color`, `lifetime`, `direction`, `spawn_spread`, `max_particles`
- `text`: `content`, `font_path`, `font_size`, `color`, `alignment`, `padding`
- `timer`: `style`, `color`, `background_color`, `corner_radius`

## License

MIT — see [LICENSE](LICENSE).

This is an independent, original implementation. The following projects provided design inspiration:

- **[wav2bar-reborn](https://github.com/Picorims/wav2bar-reborn)** by Picorims (MPL-2.0) — the multi-layer compositing model and layer-per-surface rendering approach.
- **[seewav](https://github.com/adefossez/seewav)** by Alexandre Défossez (Unlicense) — the symmetric waveform-bar visual style reproduced in the `wavebars` layer and the `wavebars-seewav-*` presets.

No source code from either project was copied or modified. The `wavebars-seewav-*` preset names are an explicit attribution to seewav's aesthetic.

## Development Notes

The planned architecture is implemented in:

- `app/audio.py`: audio loading and `FrameData` generation
- `app/compositor.py`: background creation, layer compositing, progress display
- `app/layers/`: visualiser layer implementations
- `app/effects.py`: glow, grain, and blur effects
- `app/encoder.py`: FFmpeg subprocess wrapper
- `app/presets.py`: preset and project loading
- `app/cli.py`: Typer CLI entry point

Generated media, cache directories, and local virtual environments should not be committed.
