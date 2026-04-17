from __future__ import annotations

import json
from pathlib import Path
import subprocess

from contracts.api import RequestIdentity
from runtime.bootstrap import create_application_context


def test_non_bio_dry_run_skips_scheduler_script_generation() -> None:
    context = create_application_context()

    submission = context.facade.build_dry_run_submission(
        request_text="Summarize local SOP checkpoints for data redaction",
        identity=RequestIdentity(
            task_id="task-runtime-knowledge-001",
            run_id="run-runtime-knowledge-001",
            working_directory="/cluster/work/sheep",
        ),
    )

    assert submission.run_context.task_id == "task-runtime-knowledge-001"
    assert submission.run_context.run_id == "run-runtime-knowledge-001"
    assert submission.cluster_execution_enabled is False
    assert submission.command == []
    assert submission.script_preview.startswith("scheduler_skipped:")
    assert submission.job_handle.job_id.startswith("SKIPPED-NONBIO-")
    assert submission.artifacts is not None
    assert "results" in submission.artifacts.artifact_index
    assert "reports" in submission.artifacts.artifact_index
    assert submission.artifacts.audit_record_path is not None
    assert submission.artifacts.memory_handoff_summary is not None


def test_bio_submit_preview_exposes_wrapper_poll_and_recovery_fields() -> None:
    context = create_application_context()

    submission = context.facade.build_submit_preview(
        request_text="Prepare submit preview for sheep PCA workflow",
        dry_run_completed=True,
        identity=RequestIdentity(
            task_id="task-runtime-submit-001",
            run_id="run-runtime-submit-001",
            working_directory="/cluster/work/sheep",
        ),
    )

    assert submission.mode == "submit-preview"
    assert submission.cluster_execution_enabled is True
    assert submission.run_context.task_id == "task-runtime-submit-001"
    assert submission.command[0] == "bash"
    assert submission.command[1].replace("\\", "/").endswith("scripts/pca_pipeline/run_pca_pipeline.sh")
    assert submission.scheduler_script_path is not None
    assert submission.scheduler_script_path.endswith(".sbatch.sh")
    assert submission.wrapper_path is not None
    assert submission.wrapper_path.endswith(".wrapper.sh")
    assert submission.wrapper_preview is not None
    assert "poll_hint:" in submission.wrapper_preview
    assert len(submission.poll_strategy) >= 3
    assert len(submission.failure_recovery) >= 3
    assert submission.job_handle.job_id.startswith("PLAN-SLURM-")
    assert submission.artifacts is not None
    assert "logs" in submission.artifacts.artifact_index
    assert len(submission.artifacts.artifact_index["logs"]) == 2
    assert submission.artifacts.report_summary is not None
    assert submission.artifacts.audit_record_path is not None
    assert submission.artifacts.memory_handoff_summary is not None


def test_poll_explanation_returns_structured_failed_state() -> None:
    context = create_application_context()

    poll = context.facade.explain_poll_state("SLURM-FAIL-EXAMPLE-001")

    assert poll.job_id == "SLURM-FAIL-EXAMPLE-001"
    assert poll.state.value == "failed"
    assert poll.recommended_action == "trigger_failure_recovery"
    assert poll.terminal is True


def test_bio_submit_returns_submit_mode_handle_when_real_execution_disabled() -> None:
    context = create_application_context()

    submission = context.facade.submit(
        request_text="Submit sheep PCA workflow for scheduler execution",
        dry_run_completed=True,
        identity=RequestIdentity(
            task_id="task-runtime-submit-real-001",
            run_id="run-runtime-submit-real-001",
            working_directory="/cluster/work/sheep",
        ),
    )

    assert submission.mode == "submit"
    assert submission.cluster_execution_enabled is True
    assert submission.command[0] == "bash"
    assert submission.job_handle.job_id.startswith("PLAN-SLURM-")
    assert submission.job_handle.state.value == "draft"
    assert submission.scheduler_script_path is not None


def test_bio_dry_run_prefers_report_generator_artifacts_when_available(tmp_path, monkeypatch) -> None:
    context = create_application_context()
    results_root = tmp_path / "results"
    (results_root / "qc").mkdir(parents=True)
    (results_root / "qc" / "sample_qc.tsv").write_text("sample_id\tcall_rate\nA\t0.98\n", encoding="utf-8")

    monkeypatch.setattr(
        "runtime.facade.shutil.which",
        lambda name: "bash" if name == "bash" else None,
    )

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        assert any(str(item).replace("\\", "/").endswith("run_report_generator.sh") for item in command)
        args: dict[str, str] = {}
        index = 0
        while index < len(command):
            token = str(command[index])
            if token.startswith("--") and token != "--force" and index + 1 < len(command):
                args[token] = str(command[index + 1])
                index += 2
                continue
            index += 1
        assert "--scheduler-script" in args
        assert "--wrapper" in args
        assert "--stdout-path" in args
        assert "--stderr-path" in args
        assert "--audit-path" in args
        expected_audit_suffix = "/.geneagent/audit/task-runtime-reportgen-001/run-runtime-reportgen-001.jsonl"
        assert args["--audit-path"].replace("\\", "/").endswith(expected_audit_suffix)

        workdir = Path(args["--workdir"])
        report_index = workdir / "results" / "report_index.json"
        report_index.parent.mkdir(parents=True, exist_ok=True)
        report_index.write_text(
            json.dumps(
                {
                    "schema_version": "report_index.v2",
                    "summary": {"one_line": "pca_pipeline selected; diagnostics=ok"},
                    "selected_blueprint_summary": {
                        "name": "pca_pipeline",
                        "coverage": {"required_markers": 2, "present_markers": 2, "missing_markers": []},
                    },
                    "diagnostics": {"status": "ok", "summary": "No failure indicators detected.", "signals": []},
                    "collections": {
                        "results": ["results/qc/sample_qc.tsv", "results/traceability/traceability.json"],
                        "figures": ["results/figures/pca.png"],
                        "reports": ["reports/summary_report.md", "results/traceability/traceability.md"],
                        "logs": [],
                    },
                    "artifacts": [
                        {"path": "results/qc/sample_qc.tsv", "name": "sample_qc.tsv"},
                        {"path": "results/figures/pca.png", "name": "pca.png"},
                    ],
                    "traceability": {
                        "links": [
                            {"rel": "scheduler_script", "path": args["--scheduler-script"], "exists": True},
                            {"rel": "wrapper_script", "path": args["--wrapper"], "exists": True},
                            {"rel": "stdout_log", "path": args["--stdout-path"], "exists": False},
                            {"rel": "stderr_log", "path": args["--stderr-path"], "exists": False},
                            {"rel": "audit_record", "path": args["--audit-path"], "exists": False},
                            {"rel": "traceability_json", "path": "results/traceability/traceability.json", "exists": True},
                            {"rel": "traceability_markdown", "path": "results/traceability/traceability.md", "exists": True},
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        summary_output = Path(args["--summary-output"])
        summary_output.parent.mkdir(parents=True, exist_ok=True)
        summary_output.write_text("# Summary\n", encoding="utf-8")

        traceability_dir = Path(args["--traceability-dir"])
        traceability_dir.mkdir(parents=True, exist_ok=True)
        (traceability_dir / "traceability.json").write_text("{}", encoding="utf-8")
        (traceability_dir / "traceability.md").write_text("# Traceability\n", encoding="utf-8")

        return subprocess.CompletedProcess(command, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("runtime.facade.subprocess.run", fake_run)

    submission = context.facade.build_dry_run_submission(
        request_text="Prepare dry-run for sheep PCA workflow",
        identity=RequestIdentity(
            task_id="task-runtime-reportgen-001",
            run_id="run-runtime-reportgen-001",
            working_directory=str(tmp_path),
        ),
    )

    assert submission.artifacts is not None
    assert submission.artifacts.report_summary is not None
    assert "report_generator integrated" in submission.artifacts.report_summary
    assert "diagnostics=ok" in submission.artifacts.report_summary
    assert "traceability=scheduler_script,wrapper_script,stdout_log,stderr_log" in submission.artifacts.report_summary
    assert any("summary_report.md" in path for path in submission.artifacts.report_paths)
    assert any("traceability.json" in path for path in submission.artifacts.result_paths)
    assert any(path.replace("\\", "/").endswith("/.geneagent/audit/task-runtime-reportgen-001/run-runtime-reportgen-001.jsonl") for path in submission.artifacts.result_paths)


def test_bio_dry_run_report_summary_surfaces_failure_diagnostics(tmp_path, monkeypatch) -> None:
    context = create_application_context()
    results_root = tmp_path / "results"
    (results_root / "qc").mkdir(parents=True)
    (results_root / "qc" / "sample_qc.tsv").write_text("sample_id\tcall_rate\nA\t0.98\n", encoding="utf-8")

    monkeypatch.setattr(
        "runtime.facade.shutil.which",
        lambda name: "bash" if name == "bash" else None,
    )

    def fake_run(command: list[str], **_kwargs) -> subprocess.CompletedProcess[str]:
        args: dict[str, str] = {}
        index = 0
        while index < len(command):
            token = str(command[index])
            if token.startswith("--") and token != "--force" and index + 1 < len(command):
                args[token] = str(command[index + 1])
                index += 2
                continue
            index += 1

        workdir = Path(args["--workdir"])
        report_index = workdir / "results" / "report_index.json"
        report_index.parent.mkdir(parents=True, exist_ok=True)
        report_index.write_text(
            json.dumps(
                {
                    "schema_version": "report_index.v2",
                    "summary": {"one_line": "qc_pipeline selected; diagnostics=failed"},
                    "selected_blueprint_summary": {
                        "name": "qc_pipeline",
                        "coverage": {"required_markers": 3, "present_markers": 1, "missing_markers": ["reports/qc_summary.md"]},
                    },
                    "diagnostics": {
                        "status": "failed",
                        "summary": "Failure signals were detected; inspect linked logs and rerun with recovery strategy.",
                        "signals": [{"code": "scheduler_error", "severity": "error", "source": "logs/stderr.log", "message": "sbatch: error"}],
                    },
                    "collections": {
                        "results": ["results/qc/sample_qc.tsv"],
                        "figures": [],
                        "reports": ["reports/summary_report.md"],
                        "logs": ["logs/stderr.log"],
                    },
                    "artifacts": [{"path": "results/qc/sample_qc.tsv", "name": "sample_qc.tsv"}],
                    "traceability": {"links": []},
                }
            ),
            encoding="utf-8",
        )

        summary_output = Path(args["--summary-output"])
        summary_output.parent.mkdir(parents=True, exist_ok=True)
        summary_output.write_text("# Summary\n", encoding="utf-8")

        traceability_dir = Path(args["--traceability-dir"])
        traceability_dir.mkdir(parents=True, exist_ok=True)
        (traceability_dir / "traceability.json").write_text("{}", encoding="utf-8")
        (traceability_dir / "traceability.md").write_text("# Traceability\n", encoding="utf-8")

        return subprocess.CompletedProcess(command, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("runtime.facade.subprocess.run", fake_run)

    submission = context.facade.build_dry_run_submission(
        request_text="Prepare dry-run for sheep VCF QC workflow",
        identity=RequestIdentity(
            task_id="task-runtime-reportdiag-001",
            run_id="run-runtime-reportdiag-001",
            working_directory=str(tmp_path),
        ),
    )

    assert submission.artifacts is not None
    assert submission.artifacts.report_summary is not None
    assert "diagnostics=failed" in submission.artifacts.report_summary
