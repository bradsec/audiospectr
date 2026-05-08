import numpy as np
from PIL import Image
from app.layers.particles import ParticlesLayer
from app.audio import FrameData
from app.config import ProjectConfig


def make_frame(rms=0.7):
    return FrameData(
        spectrum=np.zeros(1025), waveform=np.zeros(735),
        rms=rms, bass=rms, mid=0.2, high=0.1,
        sample_rate=22050, frame_index=0, total_frames=30,
    )


def test_particles_render_returns_rgba():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = ParticlesLayer({"width": 400, "height": 400}, project)
    result = layer.render(make_frame())
    assert result.mode == "RGBA"
    assert result.size == (400, 400)


def test_particles_accumulate_state():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = ParticlesLayer(
        {"width": 400, "height": 400, "spawn_rate": 10, "lifetime": 120},
        project,
    )
    frame = make_frame(rms=0.8)
    layer.render(frame)
    assert len(layer.particles) > 0


def test_particles_cull_out_of_bounds():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = ParticlesLayer({"width": 100, "height": 100, "lifetime": 1}, project)
    for _ in range(5):
        layer.render(make_frame())
    # With lifetime=1, all particles are culled immediately after their first update
    assert len(layer.particles) == 0


def test_particles_starts_empty():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = ParticlesLayer({"width": 400, "height": 400}, project)
    assert layer.particles == []


def test_particles_silent_frame():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = ParticlesLayer({"width": 400, "height": 400}, project)
    result = layer.render(make_frame(rms=0.0))
    assert result.mode == "RGBA"
    assert result.size == (400, 400)
    # Silence (rms=0.0) must not spawn any particles
    assert len(layer.particles) == 0


def test_particles_directional_flow():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = ParticlesLayer(
        {"width": 400, "height": 400, "flow_mode": "directional",
         "spawn_rate": 10, "lifetime": 120, "direction": 270.0},
        project,
    )
    layer.render(make_frame(rms=0.8))
    assert len(layer.particles) > 0


def test_particles_state_persists_across_frames():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = ParticlesLayer(
        {"width": 400, "height": 400, "spawn_rate": 5, "lifetime": 60},
        project,
    )
    layer.render(make_frame(rms=0.8))
    count_after_first = len(layer.particles)
    layer.render(make_frame(rms=0.8))
    count_after_second = len(layer.particles)
    # Particles from the first frame are still alive in the second
    assert count_after_second >= count_after_first


def test_default_particles_spawn_across_center_area():
    project = ProjectConfig(audio="x.mp3", output="o.mp4")
    layer = ParticlesLayer({"width": 400, "height": 400}, project)
    layer.render(make_frame(rms=0.8))
    assert len(layer.particles) >= 20
    xs = [p.x for p in layer.particles]
    ys = [p.y for p in layer.particles]
    assert max(xs) - min(xs) > 40
    assert max(ys) - min(ys) > 40
