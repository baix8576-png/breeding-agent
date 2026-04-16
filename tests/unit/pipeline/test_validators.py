from __future__ import annotations

from pipeline import InputValidator


def test_input_validator_accepts_existing_vcf(tmp_path) -> None:
    vcf_path = tmp_path / "cohort.vcf"
    vcf_path.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    report = InputValidator().validate([str(vcf_path)])

    assert report.valid is True
    assert all(issue.blocking is False for issue in report.issues)
    assert len(report.normalized_inputs) == 1
    assert report.normalized_inputs[0].data_type == "vcf"
    assert "vcf" in report.detected_types
    assert any(check.check_id == "genotype_presence" and check.status.value == "pass" for check in report.consistency_checks)
    assert report.ready_for_gate == "ready_for_design"


def test_input_validator_reports_missing_path_issue(tmp_path) -> None:
    missing_path = tmp_path / "missing_table.csv"

    snapshot = InputValidator().inspect([str(missing_path)])
    issue_codes = {issue.code for issue in snapshot.issues}

    assert "missing_path" in issue_codes
    assert snapshot.ready_for_gate == "blocked_by_validation"
    assert snapshot.to_contract_report().valid is False


def test_input_validator_checks_plink_consistency_and_metadata_alignment(tmp_path) -> None:
    bed_path = tmp_path / "cohort.bed"
    bim_path = tmp_path / "cohort.bim"
    phenotype_path = tmp_path / "trait_table.tsv"
    covariate_path = tmp_path / "covariates.tsv"
    bed_path.write_text("placeholder\n", encoding="utf-8")
    bim_path.write_text("placeholder\n", encoding="utf-8")
    phenotype_path.write_text("sample_id\ttrait\nA\t1.0\n", encoding="utf-8")
    covariate_path.write_text("sample_id\tpc1\nA\t0.1\n", encoding="utf-8")

    report = InputValidator().validate(
        {
            "task_id": "task-val-001",
            "run_id": "run-val-001",
            "species": "sheep",
            "entries": [
                {"role": "geno_bed", "path": str(bed_path)},
                {"role": "geno_bim", "path": str(bim_path)},
                {"role": "phenotype_table", "path": str(phenotype_path)},
                {"role": "covariate_table", "path": str(covariate_path)},
            ],
        }
    )

    assert report.valid is False
    assert any(issue.code == "plink_trio_incomplete" for issue in report.issues)
    assert any(
        check.check_id == "plink_trio_consistency" and check.status.value == "fail"
        for check in report.consistency_checks
    )
    assert any(
        check.check_id == "phenotype_alignment_prerequisite" and check.status.value == "pass"
        for check in report.consistency_checks
    )
    assert any(entry.role == "covariate_table" for entry in report.normalized_inputs)


def test_input_validator_flags_metadata_without_genotype_backbone(tmp_path) -> None:
    phenotype_path = tmp_path / "pheno.tsv"
    phenotype_path.write_text("sample_id\ttrait\nA\t2.0\n", encoding="utf-8")

    report = InputValidator().validate(
        {
            "species": "cattle",
            "entries": [{"role": "表型", "path": str(phenotype_path)}],
        }
    )

    assert report.valid is False
    assert any(check.check_id == "metadata_requires_genotype" and check.status.value == "fail" for check in report.consistency_checks)
    assert any(issue.code == "missing_genotype_dataset" for issue in report.issues)
