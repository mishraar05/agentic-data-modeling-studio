from dataclasses import replace

import pytest

from agentic_data_modeler.source_adapters import (
    ProfilingPolicy,
    ProfilingPolicyError,
    build_aggregate_profile_plan,
)


def _authorized_policy() -> ProfilingPolicy:
    return ProfilingPolicy(
        policy_id="GOV-001",
        policy_version="1.0.0",
        profiling_mode="RESTRICTED",
        accepted_decision_refs=("D23-03", "D23-04", "D23-05"),
        allowed_metrics=("ROW_COUNT", "NULL_COUNT", "DISTINCT_COUNT"),
        max_tables=7,
        max_attributes=62,
        max_queries=7,
        per_query_timeout_seconds=120,
        total_timeout_seconds=900,
        max_concurrency=1,
        evidence_retention_days=30,
        retain_raw_values=False,
        retain_query_text=False,
        profiler_engine="DQX",
        profiler_engine_version="0.15.0",
        allow_transient_rich_statistics=True,
        persist_generated_rules=False,
    )


def test_policy_mapping_requires_exact_fields_and_boolean_retention_flags() -> None:
    values = dict(_authorized_policy().__dict__)
    assert ProfilingPolicy.from_mapping(values) == _authorized_policy()

    values["retain_raw_values"] = "false"
    with pytest.raises(ProfilingPolicyError, match="must be boolean"):
        ProfilingPolicy.from_mapping(values)


@pytest.mark.parametrize("missing", ["D23-03", "D23-04", "D23-05"])
def test_profiling_fails_closed_without_every_human_decision(missing: str) -> None:
    policy = _authorized_policy()
    policy = replace(
        policy,
        accepted_decision_refs=tuple(
            decision for decision in policy.accepted_decision_refs if decision != missing
        ),
    )

    with pytest.raises(ProfilingPolicyError, match=missing):
        policy.validate_for_execution()


def test_metadata_only_never_authorizes_source_profiling() -> None:
    with pytest.raises(ProfilingPolicyError, match="does not authorize"):
        replace(_authorized_policy(), profiling_mode="METADATA_ONLY").validate_for_execution()


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("retain_raw_values", "raw-value retention"),
        ("retain_query_text", "query text"),
    ],
)
def test_prohibited_retention_fails_before_query_planning(
    field: str, message: str
) -> None:
    with pytest.raises(ProfilingPolicyError, match=message):
        replace(_authorized_policy(), **{field: True}).validate_for_execution()


def test_profile_plan_contains_aggregate_counts_and_no_source_values() -> None:
    plan = build_aggregate_profile_plan(
        catalog="insurance_source_discovery",
        schema="gw_pc_bronze",
        table="pc_policy",
        attributes=("policy_id", "status"),
        requested_table_count=7,
        requested_attribute_count=62,
        policy=_authorized_policy(),
    )

    assert "count(*)" in plan.query_text
    assert "AS `row_count`" in plan.query_text
    assert "count_if(`policy_id` IS NULL)" in plan.query_text
    assert "count(DISTINCT `status`)" in plan.query_text
    assert all(term not in plan.query_text.lower() for term in ("min(", "max(", "group by", "limit"))
    assert plan.query_ref.startswith("profile_query_")
    assert len(plan.metric_aliases) == 4


@pytest.mark.parametrize(
    "kwargs",
    [
        {"table": "pc_policy; DROP TABLE x"},
        {"attributes": ("policy_id", "status --")},
        {"requested_table_count": 8},
    ],
)
def test_profile_plan_rejects_unsafe_or_over_budget_scope(kwargs: dict) -> None:
    request = {
        "catalog": "insurance_source_discovery",
        "schema": "gw_pc_bronze",
        "table": "pc_policy",
        "attributes": ("policy_id", "status"),
        "requested_table_count": 7,
        "requested_attribute_count": 62,
        "policy": _authorized_policy(),
    }
    request.update(kwargs)
    with pytest.raises(ProfilingPolicyError):
        build_aggregate_profile_plan(**request)


def test_profile_plan_enforces_whole_work_package_attribute_budget() -> None:
    with pytest.raises(ProfilingPolicyError, match="attribute count"):
        build_aggregate_profile_plan(
            catalog="insurance_source_discovery",
            schema="gw_pc_bronze",
            table="pc_policy",
            attributes=("policy_id",),
            requested_table_count=7,
            requested_attribute_count=63,
            policy=_authorized_policy(),
        )


def test_row_count_cannot_be_removed_from_the_policy() -> None:
    with pytest.raises(ProfilingPolicyError, match="ROW_COUNT"):
        replace(
            _authorized_policy(),
            allowed_metrics=("NULL_COUNT", "DISTINCT_COUNT"),
        ).validate_for_execution()
