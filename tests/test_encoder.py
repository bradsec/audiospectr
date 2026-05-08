from unittest.mock import MagicMock, patch
import subprocess
import pytest
from PIL import Image
from app.encoder import Encoder
from app.config import ProjectConfig


def make_project(**kwargs):
    defaults = dict(audio="in.mp3", output="out.mp4")
    defaults.update(kwargs)
    return ProjectConfig(**defaults)


def test_encoder_builds_correct_ffmpeg_command():
    project = make_project(resolution=(1280, 720), fps=24)
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        with Encoder(project):
            pass
        cmd = mock_popen.call_args[0][0]
        kwargs = mock_popen.call_args.kwargs
    assert "-s" in cmd
    assert "1280x720" in cmd
    assert "-r" in cmd
    assert "24" in cmd
    assert "-preset" in cmd
    assert "veryfast" in cmd
    assert "-crf" in cmd
    assert "23" in cmd
    assert "out.mp4" in cmd
    assert kwargs["stderr"] is not subprocess.PIPE


def test_encoder_uses_project_crf():
    project = make_project(crf=18)
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        with Encoder(project):
            pass
        cmd = mock_popen.call_args[0][0]
    assert cmd[cmd.index("-crf") + 1] == "18"


def test_encoder_pipes_frame_bytes():
    project = make_project()
    frame = Image.new("RGB", (1920, 1080), color=(255, 0, 0))
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        with Encoder(project) as enc:
            enc.write_frame(frame)
        mock_process.stdin.write.assert_called_once_with(frame.tobytes())


def test_encoder_closes_stdin_on_exit():
    project = make_project()
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        with Encoder(project):
            pass
        mock_process.stdin.close.assert_called_once()
        mock_process.wait.assert_called_once()


def test_encoder_failure_includes_ffmpeg_stderr():
    project = make_project()
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        with pytest.raises(RuntimeError, match="synthetic ffmpeg error"):
            with Encoder(project) as enc:
                enc._stderr_file.write(b"synthetic ffmpeg error")


def test_encoder_exit_calls_wait_even_if_stdin_close_raises(mocker):
    """wait() must be called even when stdin.close() raises BrokenPipeError."""
    from app.encoder import Encoder
    from app.config import ProjectConfig, BackgroundConfig
    import subprocess

    project = ProjectConfig(
        audio="a.mp3", output="o.mp4",
        resolution=(100, 100), fps=1,
        background=BackgroundConfig(),
    )
    enc = Encoder(project)
    mock_stdin = mocker.MagicMock()
    mock_stdin.close.side_effect = BrokenPipeError("pipe broken")
    mock_proc = mocker.MagicMock()
    mock_proc.stdin = mock_stdin
    mock_proc.returncode = 1
    mock_proc.wait.return_value = None
    enc._process = mock_proc
    enc._stderr_file = mocker.MagicMock()
    enc._stderr_file.seek.return_value = None
    enc._stderr_file.tell.return_value = 0
    enc._stderr_file.read.return_value = b"ffmpeg error"

    try:
        enc.__exit__(None, None, None)
    except RuntimeError:
        pass  # expected — returncode != 0

    mock_proc.wait.assert_called_once()
