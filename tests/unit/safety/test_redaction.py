from __future__ import annotations

from safety.redaction import CloudPayloadPolicy


def test_cloud_payload_policy_drops_non_allow_list_fields() -> None:
    policy = CloudPayloadPolicy(allowed_fields=["prompt", "tool_summary"])

    review = policy.review_payload(
        {
            "prompt": "summarize scheduler error",
            "tool_summary": "sbatch failed with timeout",
            "raw_path": "D:/data/sheep/cohort.vcf.gz",
        }
    )

    assert review.allowed is False
    assert "raw_path" in review.dropped_fields
    assert review.sanitized_payload["prompt"] == "summarize scheduler error"
    assert review.violation_reasons


def test_cloud_payload_policy_redacts_paths_inside_allowed_text_fields() -> None:
    policy = CloudPayloadPolicy(allowed_fields=["prompt", "sanitized_error_log"])

    review = policy.review_payload(
        {
            "prompt": "inspect /cluster/work/demo/logs/stderr.log and C:\\work\\job.log",
            "sanitized_error_log": "path=/cluster/work/demo/logs/stderr.log",
        }
    )

    assert review.allowed is True
    assert review.redacted_fields
    assert "[REDACTED_PATH]" in str(review.sanitized_payload["prompt"])
    assert "[REDACTED_PATH]" in str(review.sanitized_payload["sanitized_error_log"])
