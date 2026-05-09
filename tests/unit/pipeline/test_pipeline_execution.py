from __future__ import annotations

from contracts.common import TaskDomain
from contracts.execution import PipelineSpec
from contracts.validation import InputBundle, InputBundleEntry
from pipeline.execution import build_execution_plan


def _analysis_targets_from_command(command: list[str]) -> list[str]:
    index = command.index("--analysis-targets")
    return command[index + 1].split(",")


def test_execution_plan_for_pca_includes_population_stats_algorithms() -> None:
    plan = build_execution_plan(
        PipelineSpec(
            name="pca_pipeline",
            domain=TaskDomain.BIOINFORMATICS,
            analysis_targets=["pca", "ld", "roh", "fst"],
        ),
        request_text="Run PCA + LD + ROH + Fst on sheep cohort",
        working_directory="/cluster/work/demo",
    )

    assert plan.pipeline_name == "pca_pipeline"
    assert plan.script_path.replace("\\", "/").endswith("scripts/pca_pipeline/run_pca_pipeline.sh")
    assert plan.command[0] == "bash"
    assert "--analysis-targets" in plan.command
    assert _analysis_targets_from_command(plan.command) == ["pca", "ld", "roh", "fst"]
    assert "plink2_pca" in plan.algorithms
    assert "plink2_r2" in plan.algorithms
    assert "plink2_homozyg" in plan.algorithms
    assert "vcftools_weir_fst" in plan.algorithms


def test_execution_plan_for_genomic_prediction_uses_v1_defaults() -> None:
    plan = build_execution_plan(
        PipelineSpec(
            name="genomic_prediction",
            domain=TaskDomain.BIOINFORMATICS,
        ),
        request_text="Run genomic prediction on cattle traits",
        working_directory="/cluster/work/demo",
    )

    assert plan.pipeline_name == "genomic_prediction"
    assert plan.script_path.replace("\\", "/").endswith("scripts/genomic_prediction/run_genomic_prediction.sh")
    assert _analysis_targets_from_command(plan.command) == ["gwas", "heritability", "genomic_prediction"]
    assert "plink2_glm" in plan.algorithms
    assert "gcta_reml" in plan.algorithms
    assert "gcta_reml_pred_rand" in plan.algorithms


def test_execution_plan_alias_resolves_population_structure_pipeline() -> None:
    plan = build_execution_plan(
        PipelineSpec(
            name="population_structure",
            domain=TaskDomain.BIOINFORMATICS,
            analysis_targets=["population_statistics"],
        ),
        request_text="Compute fst pi tajima for two populations",
        working_directory="/cluster/work/demo",
    )

    assert plan.pipeline_name == "pca_pipeline"
    assert _analysis_targets_from_command(plan.command) == ["fst", "pi", "tajima_d"]
    assert "vcftools_weir_fst" in plan.algorithms
    assert "vcftools_window_pi" in plan.algorithms
    assert "vcftools_tajima_d" in plan.algorithms


def test_execution_plan_uses_input_bundle_as_first_class_arguments() -> None:
    plan = build_execution_plan(
        PipelineSpec(
            name="genomic_prediction",
            domain=TaskDomain.BIOINFORMATICS,
            input_bundle=InputBundle(
                entries=[
                    InputBundleEntry(role="vcf", path="/data/sheep/demo.vcf.gz"),
                    InputBundleEntry(role="phenotype_table", path="/data/sheep/demo_pheno.tsv"),
                    InputBundleEntry(role="covariate_table", path="/data/sheep/demo_cov.tsv"),
                    InputBundleEntry(role="pedigree_table", path="/data/sheep/demo_pedigree.tsv"),
                ]
            ),
        ),
        request_text="Run genomic prediction on sheep cohort",
        working_directory="/cluster/work/demo",
    )

    assert "--vcf" in plan.command
    assert "/data/sheep/demo.vcf.gz" in plan.command
    assert "--phenotype" in plan.command
    assert "/data/sheep/demo_pheno.tsv" in plan.command
    assert "--covariate" in plan.command
    assert "/data/sheep/demo_cov.tsv" in plan.command
    assert "--pedigree" in plan.command
    assert "/data/sheep/demo_pedigree.tsv" in plan.command
