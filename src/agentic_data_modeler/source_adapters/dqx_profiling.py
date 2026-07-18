"""Governed projection of DQX profiler output into value-free profile evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


class DqxProfileProjectionError(ValueError):
    """Raised when DQX output cannot be safely reconciled to the frozen manifest."""


@dataclass(frozen=True, slots=True)
class DqxAttributeMetrics:
    attribute_name: str
    row_count: int
    null_count: int
    distinct_count: int


@dataclass(frozen=True, slots=True)
class DqxProfileProjection:
    """Only contract-approved aggregate metrics projected from a DQX result."""

    object_name: str
    query_ref: str
    engine_ref: str
    metrics: tuple[DqxAttributeMetrics, ...]


def dqx_profile_ref(
    *,
    catalog: str,
    schema: str,
    table: str,
    attributes: tuple[str, ...],
    policy_id: str,
    policy_version: str,
    engine_version: str,
) -> str:
    """Return a stable non-query reference for one DQX profile invocation."""

    canonical = json.dumps(
        {
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "attributes": attributes,
            "policy_id": policy_id,
            "policy_version": policy_version,
            "engine": "DQX",
            "engine_version": engine_version,
            "sampling": None,
            "limit": None,
            "persisted_metrics": ("ROW_COUNT", "NULL_COUNT", "DISTINCT_COUNT"),
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return "dqx_profile_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]


def project_dqx_summary(
    *,
    object_name: str,
    attributes: tuple[str, ...],
    summary_stats: Mapping[str, Mapping[str, Any]],
    query_ref: str,
    engine_version: str,
) -> DqxProfileProjection:
    """Discard value-bearing DQX statistics and retain exact count metrics only."""

    if not attributes or len(attributes) != len(set(attributes)):
        raise DqxProfileProjectionError("DQX projection attributes must be non-empty and unique")
    missing = sorted(set(attributes) - set(summary_stats))
    if missing:
        raise DqxProfileProjectionError(f"DQX summary is missing attributes: {missing}")

    projected: list[DqxAttributeMetrics] = []
    observed_row_counts: set[int] = set()
    for attribute in attributes:
        stats = summary_stats[attribute]
        required = ("count", "count_null", "count_distinct")
        absent = [metric for metric in required if metric not in stats]
        if absent:
            raise DqxProfileProjectionError(
                f"DQX summary for {attribute!r} is missing metrics: {absent}"
            )
        try:
            row_count = int(stats["count"])
            null_count = int(stats["count_null"])
            distinct_count = int(stats["count_distinct"])
        except (TypeError, ValueError) as exc:
            raise DqxProfileProjectionError(
                f"DQX count metrics for {attribute!r} are not integers"
            ) from exc
        if min(row_count, null_count, distinct_count) < 0:
            raise DqxProfileProjectionError("DQX count metrics must be non-negative")
        if null_count > row_count or distinct_count > row_count:
            raise DqxProfileProjectionError(
                f"DQX count metrics for {attribute!r} exceed the row count"
            )
        observed_row_counts.add(row_count)
        projected.append(
            DqxAttributeMetrics(
                attribute_name=attribute,
                row_count=row_count,
                null_count=null_count,
                distinct_count=distinct_count,
            )
        )
    if len(observed_row_counts) != 1:
        raise DqxProfileProjectionError("DQX attributes disagree on the profiled row count")

    return DqxProfileProjection(
        object_name=object_name,
        query_ref=query_ref,
        engine_ref=f"DQX@{engine_version}",
        metrics=tuple(projected),
    )
