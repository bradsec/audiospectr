import numpy as np
from PIL import Image
from app.layers.text import TextLayer
from app.audio import FrameData
from app.config import ProjectConfig


def make_frame(idx=5, total=30):
    return FrameData(
        spectrum=np.zeros(1025), waveform=np.zeros(735),
        rms=0.0, bass=0.0, mid=0.0, high=0.0,
        sample_rate=22050, frame_index=idx, total_frames=total,
    )


def test_text_render_returns_rgba():
    project = ProjectConfig(audio="x.mp3", output="o.mp4",
                             metadata={"title": "Song", "artist": "Artist"})
    layer = TextLayer({"width": 400, "height": 80, "content": "Hello"}, project)
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (400, 80)


def test_text_token_substitution():
    project = ProjectConfig(audio="x.mp3", output="o.mp4",
                             metadata={"title": "MySong", "artist": "MyArtist"})
    layer = TextLayer(
        {"width": 400, "height": 80, "content": "{artist} — {title}"},
        project,
    )
    # Ensure no exception is raised; token substitution is internal
    result = layer.render(make_frame())
    assert result is not None


def test_text_time_token_output():
    project = ProjectConfig(audio="x.mp3", output="o.mp4", fps=30)
    layer = TextLayer({"width": 400, "height": 80, "content": "{time}"}, project)
    # frame_index=89, fps=30 → (89+1)/30 = 3.0s → "0:03"
    result = layer._resolve_content("{time}", make_frame(idx=89, total=300))
    assert result == "0:03"


def test_text_alignment_center():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = TextLayer(
        {"width": 400, "height": 80, "content": "Test", "alignment": "center"},
        project,
    )
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (400, 80)


def test_text_alignment_right():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = TextLayer(
        {"width": 400, "height": 80, "content": "Test", "alignment": "right"},
        project,
    )
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (400, 80)
