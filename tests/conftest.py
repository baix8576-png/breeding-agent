"""Test bootstrap helpers for src-layout imports."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


_WSL_BRIDGE_MARKERS = (
    "e_accessdenied",
    "bash/service/createinstance",
    "windows subsystem for linux has no installed distributions",
    "wsl",
)


def _is_wsl_bridge_output(output: str) -> bool:
    normalized = output.replace("\x00", "").strip().lower()
    return any(marker in normalized for marker in _WSL_BRIDGE_MARKERS)


def _iter_bash_candidates() -> list[str]:
    candidates: list[str] = []
    env_override = os.environ.get("GENEAGENT_TEST_BASH")
    if env_override:
        candidates.append(env_override)
    which_bash = shutil.which("bash")
    if which_bash:
        candidates.append(which_bash)
    candidates.extend(
        [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\usr\bin\bash.exe",
        ]
    )
    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _is_runnable_bash(path: str) -> bool:
    path_obj = Path(path)
    if not path_obj.exists():
        return False
    try:
        probe = subprocess.run(
            [str(path_obj), "--noprofile", "--norc", "-lc", "echo geneagent-bash-ok"],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    output = f"{probe.stdout}{probe.stderr}"
    if _is_wsl_bridge_output(output):
        return False
    return probe.returncode == 0 and "geneagent-bash-ok" in output


@pytest.fixture
def bash_executable() -> str:
    for candidate in _iter_bash_candidates():
        if _is_runnable_bash(candidate):
            return candidate
    pytest.skip(
        "no runnable bash found in this Windows session; "
        "set GENEAGENT_TEST_BASH or install Git Bash for script integration tests"
    )
