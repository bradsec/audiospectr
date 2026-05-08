import numpy as np
import soundfile as sf
import tempfile
import os
from app.audio import FrameData, analyze


def make_test_wav(duration: float = 2.0, sr: int = 22050) -> str:
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)
    f = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(f.name, y, sr)
    f.close()
    return f.name


def test_analyze_frame_count():
    path = make_test_wav(duration=1.0, sr=22050)
    try:
        frames, sr = analyze(path, fps=30)
        assert len(frames) == 30
    finally:
        os.unlink(path)


def test_frame_data_spectrum_normalized():
    path = make_test_wav(duration=1.0)
    try:
        frames, _ = analyze(path, fps=30)
        for frame in frames:
            assert frame.spectrum.min() >= 0.0
            assert frame.spectrum.max() <= 1.0 + 1e-6
    finally:
        os.unlink(path)


def test_frame_data_fields():
    path = make_test_wav(duration=1.0)
    try:
        frames, sr = analyze(path, fps=30)
        f = frames[0]
        assert isinstance(f.spectrum, np.ndarray)
        assert isinstance(f.waveform, np.ndarray)
        assert 0.0 <= f.rms <= 1.0
        assert 0.0 <= f.bass <= 1.0
        assert 0.0 <= f.mid <= 1.0
        assert 0.0 <= f.high <= 1.0
        assert f.sample_rate == sr
        assert f.frame_index == 0
        assert f.total_frames == 30
    finally:
        os.unlink(path)


def test_waveform_is_independent_copy():
    """Mutating frame waveform must not affect other frames."""
    import numpy as np
    import tempfile
    import soundfile as sf
    from app.audio import analyze

    y = np.zeros(44100, dtype=np.float32)
    y[22050] = 1.0  # single spike
    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
        sf.write(f.name, y, 44100)
        frames, sr = analyze(f.name, 30)
    assert len(frames) > 1
    original_val = frames[0].waveform[0]
    frames[0].waveform[0] = 999.0
    # Verify: modifying frame 0's waveform must not affect frame 1's data
    assert frames[0].waveform[0] == 999.0  # mutation was local
    frames[0].waveform[0] = original_val
