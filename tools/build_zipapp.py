"""Reproducible, offline Python zipapp builder for the dependency-free CLI.

Excludes build caches and optional web dependencies; requires Python and FFmpeg
at runtime. Never installs packages, accesses a network, or executes media.
"""
from __future__ import annotations

import shutil
import tempfile
import tomllib
import zipapp
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text("utf8"))["project"]["version"]
TARGET = ROOT / "dist" / f"releaselab-{VERSION}.pyz"


def main() -> None:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aiwallet_zipapp_") as td:
        root = Path(td)
        src = ROOT / "src" / "aiwallet_release_lab"
        dst = root / "aiwallet_release_lab"
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
        # No fastapi/uvicorn import during normal CLI operations; 'serve' explicitly
        # requires optional web dependencies from the user's environment.
        (root / "__main__.py").write_text(
            "from aiwallet_release_lab.cli import main\nraise SystemExit(main())\n", encoding="utf8")
        zipapp.create_archive(root, TARGET, interpreter="/usr/bin/env python3", compressed=True)
    print(f"Built {TARGET.name}: {TARGET.stat().st_size} bytes")


if __name__ == "__main__":
    main()
