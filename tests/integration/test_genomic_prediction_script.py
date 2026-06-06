from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "quantitative_genetics" / "run_breeding_value_prediction.sh"


def test_breeding_value_prediction_script_fails_when_no_analysis_step_executes(
    tmp_path: Path,
    bash_executable: str,
) -> None:
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
            bash_executable,
            "--noprofile",
            "--norc",
            SCRIPT.as_posix(),
            "--workdir",
            tmp_path.as_posix(),
            "--input-root",
            input_root.as_posix(),
            "--plink-prefix",
            plink_prefix.as_posix(),
            "--phenotype",
            phenotype.as_posix(),
            "--analysis-targets",
            "unsupported_target",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    output = f"{result.stdout}{result.stderr}".replace("\x00", "")
    assert result.returncode != 0
    assert "No breeding value prediction step executed" in output
