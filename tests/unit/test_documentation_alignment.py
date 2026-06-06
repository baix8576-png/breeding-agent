from __future__ import annotations

from pathlib import Path

from api.app import create_app


ROOT = Path(".")
WORKFLOW_MAP = ROOT / "docs" / "current_workflow_file_map.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_current_workflow_file_map_is_linked_from_truth_sources() -> None:
    assert WORKFLOW_MAP.exists()

    for path in [
        ROOT / "README.md",
        ROOT / "docs" / "README.md",
        ROOT / "docs" / "v2_system_map.md",
    ]:
        assert "current_workflow_file_map.md" in _read(path), path


def test_current_workflow_file_map_covers_v2_stages_and_module_owners() -> None:
    text = _read(WORKFLOW_MAP)

    required_terms = {
        "Intake",
        "Intent + Scope",
        "Input Validation",
        "Local-first RAG",
        "Blueprint Selection",
        "Resource + Safety Gate",
        "Execution",
        "Artifact + Report",
        "Audit + Memory",
        "V2 Control Plane",
        "non-bio lightweight branch",
    }
    required_paths = {
        "src/orchestration/",
        "src/pipeline/",
        "src/scheduler/",
        "src/runtime/",
        "src/safety/",
        "src/audit/",
        "src/knowledge/",
        "src/tools/",
        "src/api/",
        "src/cli/",
        "references/",
        "scripts/",
    }

    for term in required_terms | required_paths:
        assert term in text, term


def test_current_workflow_file_map_aligns_blueprints_scripts_and_domains() -> None:
    text = _read(WORKFLOW_MAP)

    required_mappings = {
        "qc_pipeline",
        "pca_pipeline",
        "grm_builder",
        "association_mapping_gwas",
        "genomic_prediction",
        "scripts/genotype_processing/run_genotype_qc.sh",
        "scripts/population_genetics/run_population_structure_diversity.sh",
        "scripts/quantitative_genetics/run_relationship_matrix.sh",
        "scripts/association_mapping/run_gwas.sh",
        "scripts/quantitative_genetics/run_breeding_value_prediction.sh",
        "scripts/reporting_audit/run_report_generator.sh",
        "references/analysis_domains/data_preparation_qc.md",
        "references/analysis_domains/genotype_processing.md",
        "references/analysis_domains/population_structure.md",
        "references/analysis_domains/association_mapping_gwas_qtl.md",
        "references/analysis_domains/functional_genomics_annotation.md",
    }

    for mapping in required_mappings:
        assert mapping in text, mapping


def test_current_workflow_file_map_covers_remote_execution_boundaries() -> None:
    text = _read(WORKFLOW_MAP)

    for mode in [
        "local_preview",
        "ssh_shell_trusted",
        "ssh_slurm_trusted",
        "manual_sbase",
        "GENEAGENT_HPC_WORK_ROOT",
        "GENEAGENT_REMOTE_ALLOWED_WRITE_ROOTS",
        "GENEAGENT_REMOTE_SHELL_CPU_CAP",
        "watch-run",
        "resume-run",
    ]:
        assert mode in text, mode


def test_readme_remote_execution_boundary_prioritizes_pc_to_ordinary_server() -> None:
    text = _read(ROOT / "README.md")

    assert "Ordinary Linux server delivery target" in text
    assert "Deployment shape: the Agent runs on the personal computer as the control plane" in text
    assert "主要执行平台：普通 Linux 服务器" in text
    assert "主要部署平台：Linux HPC 集群（登录节点 + 计算节点）" not in text
    assert "队列系统：`SLURM / PBS / SGE`" not in text


def test_system_map_uses_current_pipeline_catalog_pack_layer() -> None:
    text = _read(ROOT / "docs" / "v2_system_map.md")

    assert "src/pipeline/catalog.py" in text
    assert "src/pipeline/packs/builtin_blueprints.py" in text
    assert "src/pipeline/workflows.py" in text
    assert "compatibility layer" in text
    assert "pipeline blueprint definitions: `src/pipeline/workflows.py`" not in text


def test_current_workflow_file_map_covers_cli_api_operational_surface() -> None:
    text = _read(WORKFLOW_MAP)

    for command_or_route in [
        "plan",
        "dry-run",
        "submit-preview",
        "submit",
        "remote-check",
        "remote-session-doctor",
        "remote-smoke",
        "watch-run",
        "resume-run",
        "audit-export",
        "production-gate",
        "release-plan",
        "final-review",
        "/tasks/draft-plan",
        "/tasks/submit-preview",
        "/tasks/remote-check",
        "/tasks/watch-run",
        "/tasks/resume-run",
        "/v2/tasks/submit",
        "/v2/release/production-gate",
    ]:
        assert command_or_route in text, command_or_route


def test_actual_cli_and_api_surface_matches_current_workflow_map() -> None:
    map_text = _read(WORKFLOW_MAP)
    cli_text = _read(ROOT / "src" / "cli" / "app.py")
    app = create_app()
    route_paths = {getattr(route, "path", "") for route in app.routes}

    expected_cli_commands = {
        "plan",
        "validate-inputs",
        "dry-run",
        "submit-preview",
        "submit",
        "poll-explain",
        "report",
        "diagnostic",
        "remote-check",
        "remote-session-doctor",
        "remote-session-open",
        "remote-session-check",
        "remote-session-close",
        "remote-session-smoke",
        "remote-password-set",
        "remote-smoke",
        "watch-run",
        "resume-run",
        "audit-export",
        "observability",
        "production-gate",
        "release-plan",
        "final-review",
    }
    expected_api_routes = {
        "/tasks/draft-plan",
        "/tasks/validate-inputs",
        "/tasks/review-action",
        "/tasks/dry-run",
        "/tasks/submit-preview",
        "/tasks/submit",
        "/tasks/poll-explain",
        "/tasks/report",
        "/tasks/diagnostic",
        "/tasks/remote-check",
        "/tasks/watch-run",
        "/tasks/resume-run",
        "/tasks/audit-export",
        "/v2/tasks/draft-plan",
        "/v2/tasks/dry-run",
        "/v2/tasks/submit-preview",
        "/v2/tasks/submit",
        "/v2/tasks/poll-explain",
        "/v2/tasks/report",
        "/v2/tasks/diagnostic",
        "/v2/tasks/remote-check",
        "/v2/tasks/watch-run",
        "/v2/tasks/resume-run",
        "/v2/tasks/audit-export",
        "/v2/release/production-gate",
        "/v2/release/plan",
        "/v2/release/final-review",
    }

    for command in expected_cli_commands:
        assert f'@app.command("{command}")' in cli_text, command
        assert command in map_text, command
    assert expected_api_routes <= route_paths
    for route in expected_api_routes:
        assert route in map_text, route


def test_every_v2_task_route_is_documented_in_workflow_map_and_readme() -> None:
    app = create_app()
    route_paths = {getattr(route, "path", "") for route in app.routes}
    workflow_map_text = _read(WORKFLOW_MAP)
    readme_text = _read(ROOT / "README.md")
    system_map_text = _read(ROOT / "docs" / "v2_system_map.md")

    v1_task_routes = sorted(
        path
        for path in route_paths
        if path.startswith("/tasks/")
    )
    expected_v2_routes = {f"/v2{path}" for path in v1_task_routes}

    assert expected_v2_routes <= route_paths
    for route in sorted(expected_v2_routes):
        assert route in workflow_map_text, route
        assert route in readme_text, route
        assert route in system_map_text, route


def test_operator_auth_remote_session_commands_are_documented_as_cli_only() -> None:
    readme_text = _read(ROOT / "README.md")
    workflow_map_text = _read(WORKFLOW_MAP)
    system_map_text = _read(ROOT / "docs" / "v2_system_map.md")

    cli_only_statement = "CLI-only operator-auth commands"
    for text in [readme_text, workflow_map_text, system_map_text]:
        assert cli_only_statement in text

    assert "New CLI/API surface: `remote-session-doctor`" not in readme_text


def test_current_entrypoint_and_runtime_docstrings_use_v2_wording() -> None:
    current_stage_files = [
        ROOT / "src" / "cli" / "app.py",
        ROOT / "src" / "api" / "routes" / "tasks.py",
        ROOT / "src" / "runtime" / "bootstrap.py",
        ROOT / "src" / "runtime" / "settings.py",
        ROOT / "src" / "contracts" / "__init__.py",
    ]

    for path in current_stage_files:
        text = _read(path)
        first_lines = "\n".join(text.splitlines()[:5])
        assert "GeneAgent V1" not in first_lines, path
        assert "V1 workflows" not in first_lines, path
        assert "GeneAgent V2" in first_lines, path
