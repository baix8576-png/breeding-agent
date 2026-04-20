from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "genomic_prediction" / "run_genomic_prediction.sh"


def test_genomic_prediction_script_fails_when_no_analysis_step_executes(tmp_path: Path) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available in the current test environment")

    input_root = tmp_path / "inputs"
    input_root.mkdir(parents=True, exist_ok=True)
    plink_prefix = input_root / "demo_dataset"
    (input_root / "demo_dataset.bed").write_text("bed\n", encoding="utf-8")
    (input_root / "demo_dataset.bim").write_text("bim\n", encoding="utf-8")
    (input_root / "demo_dataset.fam").write_text("A A 0 0 0 -9\n", encoding="utf-8")
    phenotype = input_root / "demo_pheno.tsv"
    phenotype.write_text("fid\tiid\ttrait\nA\tA\t1.0\n", encoding="utf-8")

    result = subprocess.run(
        [
            bash,
            "--noprofile",
            "--norc",
            SCRIPT.as_posix(),
            "--workdir",
            str(tmp_path),
            "--input-root",
            str(input_root),
            "--plink-prefix",
            str(plink_prefix),
            "--phenotype",
            str(phenotype),
            "--analysis-targets",
            "unsupported_target",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = f"{result.stdout}{result.stderr}".replace("\x00", "")
    if result.returncode != 0 and (
        "E_ACCESSDENIED" in output
        or "Bash/Service/CreateInstance" in output
    ):
        pytest.skip("bash is present but WSL bash service is unavailable in this Windows session")

    assert result.returncode != 0
    assert "No genomic prediction step executed" in output
