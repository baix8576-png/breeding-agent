from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
BUILD_INDEX_SCRIPT = ROOT / "scripts" / "report_generator" / "build_result_index.sh"


def test_build_result_index_emits_v2_required_keys(tmp_path: Path) -> None:
    bash = shutil.which("bash")
    if bash is None:
        pytest.skip("bash is not available in the current test environment")

    workdir = tmp_path
    results_root = workdir / "results"
    reports_root = workdir / "reports"
    logs_root = workdir / "logs"
    results_root.mkdir(parents=True, exist_ok=True)
    reports_root.mkdir(parents=True, exist_ok=True)
    logs_root.mkdir(parents=True, exist_ok=True)

    (results_root / "qc").mkdir(parents=True, exist_ok=True)
    (results_root / "qc" / "sample_qc.tsv").write_text("sample_id\tcall_rate\nA\t0.98\n", encoding="utf-8")
    (reports_root / "qc_summary.md").write_text("# QC Summary\n", encoding="utf-8")
    scheduler_script = logs_root / "job.sbatch.sh"
    wrapper_script = logs_root / "job.wrapper.sh"
    stdout_log = logs_root / "stdout.log"
    stderr_log = logs_root / "stderr.log"
    scheduler_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    wrapper_script.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    stdout_log.write_text("running\n", encoding="utf-8")
    stderr_log.write_text("sbatch: error: Job failed due to scheduler issue\n", encoding="utf-8")
    audit_record = workdir / ".geneagent" / "audit" / "task-script-v2-001" / "run-script-v2-001.jsonl"
    audit_record.parent.mkdir(parents=True, exist_ok=True)
    audit_record.write_text("{\"event\":\"execution_closure\"}\n", encoding="utf-8")

    output_path = results_root / "report_index.json"
    result = subprocess.run(
        [
            bash,
            "--noprofile",
            "--norc",
            BUILD_INDEX_SCRIPT.as_posix(),
            "--workdir",
            str(workdir),
            "--results-root",
            str(results_root),
            "--pipeline",
            "qc_pipeline",
            "--task-id",
            "task-script-v2-001",
            "--run-id",
            "run-script-v2-001",
            "--job-id",
            "12345",
            "--job-state",
            "failed",
            "--submit-command",
            "sbatch logs/job.sbatch.sh",
            "--scheduler-script",
            str(scheduler_script),
            "--wrapper",
            str(wrapper_script),
            "--stdout-path",
            str(stdout_log),
            "--stderr-path",
            str(stderr_log),
            "--audit-path",
            str(audit_record),
            "--log-path",
            str(stderr_log),
            "--output",
            str(output_path),
            "--force",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output = f"{result.stdout}{result.stderr}".replace("\x00", "")
    if result.returncode != 0 and ("E_ACCESSDENIED" in output or "Bash/Service/CreateInstance" in output):
        pytest.skip("bash is present but WSL bash service is unavailable in this Windows session")

    assert result.returncode == 0, result.stderr or result.stdout
    assert output_path.is_file()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "report_index.v2"
    assert "run_context" in payload
    assert "collections" in payload
    assert "blueprint_summary" in payload
    assert "diagnostics" in payload
    assert "traceability" in payload
    assert "summary" in payload
    assert set(payload["blueprint_summary"]).issuperset({"qc", "pca", "grm", "genomic_prediction"})
    assert payload["diagnostics"]["status"] == "failed"
    assert payload["diagnostics"]["failure_tasks"] == ["12345"]

    links = payload["traceability"]["links"]
    assert isinstance(links, list)
    rels = {item["rel"] for item in links if isinstance(item, dict)}
    assert rels.issuperset(
        {
            "scheduler_script",
            "wrapper_script",
            "stdout_log",
            "stderr_log",
            "audit_record",
            "traceability_json",
            "traceability_markdown",
        }
    )
