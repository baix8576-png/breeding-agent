from __future__ import annotations

from pipeline import InputValidator


def test_input_validator_accepts_existing_vcf(tmp_path) -> None:
    vcf_path = tmp_path / "cohort.vcf"
    vcf_path.write_text("##fileformat=VCFv4.2\n", encoding="utf-8")

    report = InputValidator().validate([str(vcf_path)])

    assert report.valid is True
    assert report.issues == []


def test_input_validator_reports_missing_path_issue(tmp_path) -> None:
    missing_path = tmp_path / "missing_table.csv"

    snapshot = InputValidator().inspect([str(missing_path)])
    issue_codes = {issue.code for issue in snapshot.issues}

    assert "missing_path" in issue_codes
    assert snapshot.ready_for_gate == "blocked_by_validation"
    assert snapshot.to_contract_report().valid is False
