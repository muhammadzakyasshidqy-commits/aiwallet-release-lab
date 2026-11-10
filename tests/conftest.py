import subprocess
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def sample_video(tmp_path_factory) -> Path:
    p = tmp_path_factory.mktemp("media") / "portrait_sample.mp4"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
           "-i", "testsrc2=size=480x854:rate=24:duration=3.2", "-f", "lavfi",
           "-i", "sine=frequency=440:sample_rate=48000:duration=3.2", "-map", "0:v",
           "-map", "1:a", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-shortest", str(p)]
    subprocess.run(cmd, check=True, timeout=35)
    return p


@pytest.fixture(scope="session")
def black_video(tmp_path_factory) -> Path:
    p = tmp_path_factory.mktemp("media") / "black.mp4"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
           "-i", "color=c=black:s=360x640:r=24:d=3", "-an", "-c:v", "libx264",
           "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(p)]
    subprocess.run(cmd, check=True, timeout=30)
    return p
