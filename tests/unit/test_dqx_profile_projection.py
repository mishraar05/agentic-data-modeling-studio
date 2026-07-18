import pytest

from agentic_data_modeler.source_adapters import (
    DqxProfileProjectionError,
    dqx_profile_ref,
    project_dqx_summary,
)


def test_dqx_projection_retains_only_approved_count_metrics() -> None:
    projection = project_dqx_summary(
        object_name="pc_policy",
        attributes=("policy_id", "status"),
        summary_stats={
            "policy_id": {
                "count": 10,
                "count_null": 0,
                "count_distinct": 10,
                "min": 1001,
                "max": 1010,
                "mean": 1005.5,
            },
            "status": {
                "count": 10,
                "count_null": 1,
                "count_distinct": 3,
                "min": "ACTIVE",
                "max": "RENEWED",
            },
        },
        query_ref="dqx_profile_123",
        engine_version="0.15.0",
    )
    assert projection.engine_ref == "DQX@0.15.0"
    assert projection.metrics[1].null_count == 1
    assert not hasattr(projection.metrics[1], "min")
    assert not hasattr(projection.metrics[1], "max")


def test_dqx_projection_requires_complete_consistent_metrics() -> None:
    with pytest.raises(DqxProfileProjectionError, match="missing metrics"):
        project_dqx_summary(
            object_name="pc_policy",
            attributes=("policy_id",),
            summary_stats={"policy_id": {"count": 10, "count_null": 0}},
            query_ref="dqx_profile_123",
            engine_version="0.15.0",
        )


def test_dqx_profile_reference_is_stable_and_scope_sensitive() -> None:
    values = {
        "catalog": "insurance",
        "schema": "policycenter",
        "table": "pc_policy",
        "attributes": ("policy_id", "status"),
        "policy_id": "GOV-001",
        "policy_version": "1.0.0",
        "engine_version": "0.15.0",
    }
    first = dqx_profile_ref(**values)
    assert first == dqx_profile_ref(**values)
    assert first != dqx_profile_ref(**{**values, "table": "pc_vehicle"})
