from __future__ import annotations

from pathlib import Path


SCRIPT_ROOT = Path("scripts")


def test_bio_scripts_have_explicit_resource_controls() -> None:
    scripts = sorted(SCRIPT_ROOT.glob("*/*.sh"))

    assert scripts
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        first_line = text.splitlines()[0]

        assert first_line == "#!/usr/bin/env bash", script
        assert "set -euo pipefail" in text, script
        assert "THREAD" in text or "CPU" in text or "NTHREADS" in text, script
        assert (
            "--threads" in text
            or "--thread" in text
            or "OMP_NUM_THREADS" in text
            or "OPENBLAS_NUM_THREADS" in text
        ), script
        assert "RESULT" in text or "OUTPUT" in text or "OUT_DIR" in text, script


def test_operation_guides_link_to_knowledge_assets() -> None:
    guides = sorted(SCRIPT_ROOT.glob("*/operation_guide.md"))

    assert guides
    for guide in guides:
        text = guide.read_text(encoding="utf-8")

        assert "references/sop/" in text, guide
        assert "references/parameter_playbooks/" in text, guide
        assert "references/failure_cases/" in text or "references/evaluation/diagnostics/" in text, guide
