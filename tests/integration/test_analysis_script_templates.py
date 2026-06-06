from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"

ANALYSIS_SCRIPTS = [
    ("genotype_qc", SCRIPTS / "genotype_processing" / "run_genotype_qc.sh", Path("results/qc")),
    (
        "population_structure_diversity",
        SCRIPTS / "population_genetics" / "run_population_structure_diversity.sh",
        Path("results/structure"),
    ),
    (
        "relationship_matrix",
        SCRIPTS / "quantitative_genetics" / "run_relationship_matrix.sh",
        Path("results/grm"),
    ),
    (
        "breeding_value_prediction",
        SCRIPTS / "quantitative_genetics" / "run_breeding_value_prediction.sh",
        Path("results/prediction"),
    ),
    (
        "association_mapping_gwas",
        SCRIPTS / "association_mapping" / "run_gwas.sh",
        Path("results/association/gwas"),
    ),
]


TOOL_RESOURCE_SNIPPETS = {
    "genotype_qc": [
        'plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB"',
        'plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB"',
        'bcftools stats --threads "$THREADS" "$VCF_PATH"',
    ],
    "population_structure_diversity": [
        'plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB"',
        'plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --indep-pairwise',
        'plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --extract',
        'plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --homozyg',
    ],
    "relationship_matrix": [
        'plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB"',
        'plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --make-rel',
        'gcta64 --bfile "$PLINK_PREFIX" --thread-num "$THREADS"',
    ],
    "breeding_value_prediction": [
        'plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB"',
        'gcta64 --bfile "$PLINK_PREFIX" --thread-num "$THREADS"',
        'gcta64 --grm "$H2_DIR/grm" --thread-num "$THREADS"',
    ],
    "association_mapping_gwas": [
        'plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB"',
        'gwas_cmd=(plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB"',
    ],
}


def test_scripts_use_scientific_domain_directories_not_legacy_pipeline_directories() -> None:
    expected_dirs = {
        "genotype_processing",
        "population_genetics",
        "quantitative_genetics",
        "association_mapping",
        "reporting_audit",
    }
    legacy_dirs = {
        "qc_pipeline",
        "pca_pipeline",
        "grm_builder",
        "genomic_prediction",
        "report_generator",
    }

    assert expected_dirs.issubset({path.name for path in SCRIPTS.iterdir() if path.is_dir()})
    assert legacy_dirs.isdisjoint({path.name for path in SCRIPTS.iterdir() if path.is_dir()})


@pytest.mark.parametrize(("pipeline_name", "script_path", "_output_rel"), ANALYSIS_SCRIPTS)
def test_analysis_script_templates_have_static_template_contract(
    pipeline_name: str,
    script_path: Path,
    _output_rel: Path,
) -> None:
    text = script_path.read_text(encoding="utf-8")
    for expected in [
        "--task-id",
        "--run-id",
        "--session-id",
        "--threads",
        "--memory-mb",
        "--tmp-dir",
        "--log-dir",
        "--dry-run",
        "--force",
        "analysis_script_template.v1",
        "analysis_script_audit_sidecar.v1",
        "write_run_manifest",
        "write_audit_sidecar",
        "scheduler_managed_externally",
        "apply_resource_limits",
        "ulimit -v",
        'export TMPDIR="$TMP_DIR"',
        '"memory_mb": $MEMORY_MB',
        '"tmp_dir":',
    ]:
        assert expected in text, f"{pipeline_name} missing template contract token: {expected}"


@pytest.mark.parametrize(("pipeline_name", "script_path", "_output_rel"), ANALYSIS_SCRIPTS)
def test_analysis_script_templates_constrain_tool_threads_and_memory(
    pipeline_name: str,
    script_path: Path,
    _output_rel: Path,
) -> None:
    text = script_path.read_text(encoding="utf-8")
    for expected in TOOL_RESOURCE_SNIPPETS[pipeline_name]:
        assert expected in text, f"{pipeline_name} missing bounded tool command snippet: {expected}"


@pytest.mark.parametrize(("pipeline_name", "script_path", "_output_rel"), ANALYSIS_SCRIPTS)
def test_analysis_script_templates_do_not_emit_unbounded_supported_tool_commands(
    pipeline_name: str,
    script_path: Path,
    _output_rel: Path,
) -> None:
    text = script_path.read_text(encoding="utf-8")
    checked_lines = 0

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("plink2 ") or "(plink2 " in line:
            checked_lines += 1
            assert '--threads "$THREADS"' in line, f"{pipeline_name} has unbounded PLINK2 thread use: {line}"
            assert '--memory "$MEMORY_MB"' in line, f"{pipeline_name} has unbounded PLINK2 memory use: {line}"
        elif line.startswith("gcta64 "):
            checked_lines += 1
            assert '--thread-num "$THREADS"' in line, f"{pipeline_name} has unbounded GCTA thread use: {line}"
        elif line.startswith("bcftools stats "):
            checked_lines += 1
            assert '--threads "$THREADS"' in line, f"{pipeline_name} has unbounded bcftools stats use: {line}"

    assert checked_lines > 0, f"{pipeline_name} had no supported tool invocations to audit"


def test_report_generator_has_static_dry_run_template_contract() -> None:
    text = (SCRIPTS / "reporting_audit" / "run_report_generator.sh").read_text(encoding="utf-8")
    for expected in [
        "--task-id",
        "--run-id",
        "--session-id",
        "--log-dir",
        "--dry-run",
        "--force",
        "analysis_script_template.v1",
        "report_generator_run_manifest.json",
        "write_run_manifest",
    ]:
        assert expected in text


@pytest.mark.parametrize(("pipeline_name", "script_path", "_output_rel"), ANALYSIS_SCRIPTS)
def test_analysis_script_templates_expose_common_runtime_options(
    pipeline_name: str,
    script_path: Path,
    _output_rel: Path,
    bash_executable: str,
) -> None:
    result = subprocess.run(
        [bash_executable, "--noprofile", "--norc", script_path.as_posix(), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    output = f"{result.stdout}{result.stderr}".lower()
    assert result.returncode == 0, output
    for option in [
        "--task-id",
        "--run-id",
        "--session-id",
        "--threads",
        "--memory-mb",
        "--tmp-dir",
        "--log-dir",
        "--dry-run",
        "--force",
    ]:
        assert option in output, f"{pipeline_name} missing {option}"


@pytest.mark.parametrize(("pipeline_name", "script_path", "output_rel"), ANALYSIS_SCRIPTS)
def test_analysis_script_dry_run_writes_manifest_and_audit_sidecar(
    pipeline_name: str,
    script_path: Path,
    output_rel: Path,
    tmp_path: Path,
    bash_executable: str,
) -> None:
    input_root = tmp_path / "inputs"
    input_root.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            bash_executable,
            "--noprofile",
            "--norc",
            script_path.as_posix(),
            "--workdir",
            tmp_path.as_posix(),
            "--input-root",
            input_root.as_posix(),
            "--task-id",
            f"task-template-{pipeline_name}",
            "--run-id",
            f"run-template-{pipeline_name}",
            "--session-id",
            "session-template-001",
            "--threads",
            "3",
            "--memory-mb",
            "1234",
            "--tmp-dir",
            (tmp_path / "tmp" / pipeline_name).as_posix(),
            "--log-dir",
            (tmp_path / "logs").as_posix(),
            "--analysis-targets",
            "template_check",
            "--request-text",
            f"Dry-run template check for {pipeline_name}",
            "--dry-run",
            "--force",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    output = f"{result.stdout}{result.stderr}"
    assert result.returncode == 0, output

    manifest_path = tmp_path / output_rel / "run_manifest.json"
    audit_path = tmp_path / output_rel / "audit_sidecar.json"
    log_path = tmp_path / "logs" / f"{pipeline_name}.log"
    assert manifest_path.is_file()
    assert audit_path.is_file()
    assert log_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "analysis_script_template.v1"
    assert manifest["pipeline"] == pipeline_name
    assert manifest["mode"] == "dry_run"
    assert manifest["threads"] == 3
    assert manifest["memory_mb"] == 1234
    assert manifest["tmp_dir"] == (tmp_path / "tmp" / pipeline_name).as_posix()
    assert manifest["run_context"]["task_id"] == f"task-template-{pipeline_name}"
    assert manifest["run_context"]["run_id"] == f"run-template-{pipeline_name}"
    assert manifest["safety"]["scheduler_managed_externally"] is True
    assert audit["schema_version"] == "analysis_script_audit_sidecar.v1"
    assert audit["pipeline"] == pipeline_name
    assert audit["mode"] == "dry_run"


def test_report_generator_dry_run_writes_manifest(
    tmp_path: Path,
    bash_executable: str,
) -> None:
    script_path = SCRIPTS / "reporting_audit" / "run_report_generator.sh"
    (tmp_path / "results").mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            bash_executable,
            "--noprofile",
            "--norc",
            script_path.as_posix(),
            "--workdir",
            tmp_path.as_posix(),
            "--task-id",
            "task-report-template",
            "--run-id",
            "run-report-template",
            "--session-id",
            "session-report-template",
            "--log-dir",
            (tmp_path / "logs").as_posix(),
            "--dry-run",
            "--force",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    output = f"{result.stdout}{result.stderr}"
    assert result.returncode == 0, output
    manifest_path = tmp_path / "results" / "report_generator_run_manifest.json"
    log_path = tmp_path / "logs" / "report_generator.log"
    assert manifest_path.is_file()
    assert log_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "analysis_script_template.v1"
    assert manifest["pipeline"] == "report_generator"
    assert manifest["mode"] == "dry_run"
    assert manifest["run_context"]["task_id"] == "task-report-template"
