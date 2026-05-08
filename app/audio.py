from __future__ import annotations
import numpy as np
import librosa
from dataclasses import dataclass


@dataclass
class FrameData:
    spectrum: np.ndarray      # shape (n_bins,), normalized 0.0–1.0
    waveform: np.ndarray      # shape (hop_length,), raw amplitude
    rms: float                # 0.0–1.0
    bass: float               # 20–250 Hz band mean, 0.0–1.0
    mid: float                # 250–4000 Hz band mean, 0.0–1.0
    high: float               # 4000–20000 Hz band mean, 0.0–1.0
    sample_rate: int
    frame_index: int
    total_frames: int


def analyze(path: str, fps: int) -> tuple[list[FrameData], int]:
    if fps <= 0:
        raise ValueError(f"fps must be positive, got {fps}")
    try:
        y, sr = librosa.load(path, sr=None, mono=True)
    except Exception as e:
        raise RuntimeError(f"Could not load audio file '{path}': {e}") from e
    hop_length = max(1, sr // fps)
    n_fft = 2048

    # center=True (librosa default) pads audio so STFT frames align with audio
    stft = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, center=True)
    magnitude = np.abs(stft)                      # (1025, n_stft_frames)

    max_mag = magnitude.max()
    if max_mag > 0:
        magnitude = magnitude / max_mag

    rms_frames = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    rms_max = rms_frames.max()
    if rms_max > 0:
        rms_frames = rms_frames / rms_max

    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    bass_mask = (freqs >= 20) & (freqs <= 250)
    mid_mask  = (freqs > 250) & (freqs <= 4000)
    high_mask = (freqs > 4000) & (freqs <= 20000)

    # Derive expected frame count from audio duration
    expected_frames = int(np.ceil(len(y) / hop_length))
    n_stft = magnitude.shape[1]
    total_frames = min(expected_frames, n_stft)

    frames: list[FrameData] = []
    for i in range(total_frames):
        spec = magnitude[:, i].copy()

        start = i * hop_length
        wave = y[start : start + hop_length]
        if len(wave) < hop_length:
            wave = np.pad(wave, (0, hop_length - len(wave)))
        else:
            wave = wave.copy()

        rms_val = float(rms_frames[i]) if i < len(rms_frames) else 0.0

        frames.append(FrameData(
            spectrum=spec,
            waveform=wave,
            rms=rms_val,
            bass=float(spec[bass_mask].mean()) if bass_mask.any() else 0.0,
            mid=float(spec[mid_mask].mean())  if mid_mask.any()  else 0.0,
            high=float(spec[high_mask].mean()) if high_mask.any() else 0.0,
            sample_rate=sr,
            frame_index=i,
            total_frames=total_frames,
        ))

    return frames, sr
