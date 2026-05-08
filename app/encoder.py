from __future__ import annotations
import subprocess
import sys
import tempfile
from PIL import Image
from app.config import ProjectConfig


class Encoder:
    def __init__(self, project: ProjectConfig) -> None:
        self._project = project
        self._process: subprocess.Popen | None = None
        self._stderr_file: tempfile._TemporaryFileWrapper | None = None

    def __enter__(self) -> "Encoder":
        w, h = self._project.resolution
        self._stderr_file = tempfile.TemporaryFile()
        cmd = [
            "ffmpeg", "-y",
            "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{w}x{h}",
            "-r", str(self._project.fps),
            "-pix_fmt", "rgb24",
            "-i", "pipe:0",
            "-i", self._project.audio,
            "-c:v", "libx264",
            "-preset", self._project.video_preset,
            "-crf", str(self._project.crf),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            self._project.output,
        ]
        self._process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=self._stderr_file,
        )
        return self

    def write_frame(self, frame: Image.Image) -> None:
        if not self._process or not self._process.stdin:
            raise RuntimeError("Encoder stdin is not available")
        self._process.stdin.write(frame.tobytes())

    def __exit__(self, exc_type: object, *_: object) -> None:
        if self._process:
            if self._process.stdin:
                try:
                    self._process.stdin.close()
                except OSError:
                    pass
            try:
                self._process.wait(timeout=60)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            if self._process.returncode != 0:
                stderr = _read_stderr_tail(self._stderr_file)
                if self._stderr_file:
                    self._stderr_file.close()
                ffmpeg_error = RuntimeError(
                    f"FFmpeg exited with code {self._process.returncode}\n{stderr}"
                )
                if exc_type is None:
                    raise ffmpeg_error
                print(f"[encoder] FFmpeg also failed: {ffmpeg_error}", file=sys.stderr)
                return
        if self._stderr_file:
            self._stderr_file.close()


def _read_stderr_tail(stderr_file: object | None, max_bytes: int = 4000) -> str:
    if stderr_file is None:
        return ""
    stderr_file.seek(0, 2)
    size = stderr_file.tell()
    stderr_file.seek(max(0, size - max_bytes))
    return stderr_file.read().decode("utf-8", errors="replace")
