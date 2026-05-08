import numpy as np
from PIL import Image
from app.layers.timer import TimerLayer
from app.audio import FrameData
from app.config import ProjectConfig


def make_frame(idx, total):
    return FrameData(
        spectrum=np.zeros(1025), waveform=np.zeros(735),
        rms=0.0, bass=0.0, mid=0.0, high=0.0,
        sample_rate=22050, frame_index=idx, total_frames=total,
    )


def test_timer_render_returns_rgba():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = TimerLayer({"width": 400, "height": 20}, project)
    result = layer.render(make_frame(10, 100))
    assert result.mode == "RGBA"
    assert result.size == (400, 20)
    pixels = np.array(result)
    assert tuple(pixels[pixels[:, :, 3] > 0][0][:3]) == (255, 255, 255)


def test_timer_at_start_has_narrow_bar():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = TimerLayer({"width": 400, "height": 20, "color": "#ffffff"}, project)
    result_start = layer.render(make_frame(0, 100))
    result_end   = layer.render(make_frame(99, 100))
    arr_start = np.array(result_start)
    arr_end   = np.array(result_end)
    # End frame should have more filled pixels than start frame
    assert arr_end[:, :, 3].sum() >= arr_start[:, :, 3].sum()


def test_timer_line_style():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = TimerLayer({"width": 400, "height": 20, "style": "line"}, project)
    # Mid-point frame
    result_mid = layer.render(make_frame(50, 100))
    assert result_mid.mode == "RGBA"
    # Last frame — should not crash and indicator should be visible (clamped to width-1)
    result_end = layer.render(make_frame(99, 100))
    arr = np.array(result_end)
    assert arr[:, :, 3].max() > 0


def test_timer_line_indicator_position():
    """Line indicator must be near x=200 for 50% progress on a 400-wide layer."""
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = TimerLayer({"width": 400, "height": 20, "style": "line", "color": "#ffffff"}, project)
    result = layer.render(make_frame(50, 100))
    assert result.size == (400, 20)
    arr = np.array(result)
    nonzero_cols = np.where(arr[:, :, 3] > 0)[1]
    assert len(nonzero_cols) > 0, "No visible pixels drawn"
    center_x = int(np.median(nonzero_cols))
    assert abs(center_x - 200) <= 5, f"Line indicator at x={center_x}, expected ~200 for 50% progress"
