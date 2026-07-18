"""Fail-closed planning boundary for controlled source profiling.

This module does not execute SQL. It proves that a proposed profiling request
is bounded by accepted human decisions before producing an ephemeral,
aggregate-only query plan for a read-only adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re


_SEMANTIC_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_REQUIRED_DECISIONS = frozenset({"D23-03", "D23-04", "D23-05"})
_SAFE_METRICS = frozenset({"ROW_COUNT", "NULL_COUNT", "DISTINCT_COUNT"})
_TEMPLATE_VERSION = "restricted-aggregate/0.1.0"


class ProfilingPolicyError(ValueError):
    """Raised before query planning when profiling authority is incomplete."""


@dataclass(frozen=True)
class ProfilingPolicy:
    """Human-approved limits consumed by the deterministic profiling tool."""

    policy_id: str
    policy_version: str
    profiling_mode: str
    accepted_decision_refs: tuple[str, ...]
    allowed_metrics: tuple[str, ...]
    max_tables: int
    max_attributes: int
    max_queries: int
    per_query_timeout_seconds: int
    total_timeout_seconds: int
    max_concurrency: int
    evidence_retention_days: int
    retain_raw_values: bool
    retain_query_text: bool
    profiler_engine: str
    profiler_engine_version: str
    allow_transient_rich_statistics: bool
    persist_generated_rules: bool

    @classmethod
    def from_mapping(cls, values: dict) -> "ProfilingPolicy":
        """Create and validate a policy projection loaded from governed JSON."""

        required = {field.name for field in cls.__dataclass_fields__.values()}
        missing = sorted(required.difference(values))
        unexpected = sorted(set(values).difference(required))
        if missing or unexpected:
            raise ProfilingPolicyError(
                f"profiling policy fields mismatch; missing={missing}, unexpected={unexpected}"
            )
        try:
            policy = cls(
                policy_id=str(values["policy_id"]),
                policy_version=str(values["policy_version"]),
                profiling_mode=str(values["profiling_mode"]),
                accepted_decision_refs=tuple(values["accepted_decision_refs"]),
                allowed_metrics=tuple(values["allowed_metrics"]),
                max_tables=int(values["max_tables"]),
                max_attributes=int(values["max_attributes"]),
                max_queries=int(values["max_queries"]),
                per_query_timeout_seconds=int(values["per_query_timeout_seconds"]),
                total_timeout_seconds=int(values["total_timeout_seconds"]),
                max_concurrency=int(values["max_concurrency"]),
                evidence_retention_days=int(values["evidence_retention_days"]),
                retain_raw_values=values["retain_raw_values"],
                retain_query_text=values["retain_query_text"],
                profiler_engine=str(values["profiler_engine"]),
                profiler_engine_version=str(values["profiler_engine_version"]),
                allow_transient_rich_statistics=values["allow_transient_rich_statistics"],
                persist_generated_rules=values["persist_generated_rules"],
            )
        except (TypeError, ValueError) as exc:
            raise ProfilingPolicyError("profiling policy contains invalid field types") from exc
        if not isinstance(policy.retain_raw_values, bool) or not isinstance(
            policy.retain_query_text, bool
        ):
            raise ProfilingPolicyError("profiling retention flags must be boolean")
        if not isinstance(policy.allow_transient_rich_statistics, bool) or not isinstance(
            policy.persist_generated_rules, bool
        ):
            raise ProfilingPolicyError("profiling engine flags must be boolean")
        policy.validate_for_execution()
        return policy

    def validate_for_execution(self) -> None:
        if not self.policy_id.strip():
            raise ProfilingPolicyError("profiling policy ID is required")
        if not _SEMANTIC_VERSION.fullmatch(self.policy_version):
            raise ProfilingPolicyError("profiling policy version must be semantic X.Y.Z")
        if self.profiling_mode == "METADATA_ONLY":
            raise ProfilingPolicyError("METADATA_ONLY does not authorize source profiling")
        if self.profiling_mode != "RESTRICTED":
            raise ProfilingPolicyError(
                "the first proof slice accepts only contract-owned RESTRICTED mode"
            )

        missing = _REQUIRED_DECISIONS.difference(self.accepted_decision_refs)
        if missing:
            raise ProfilingPolicyError(
                f"accepted profiling decisions are missing: {sorted(missing)}"
            )
        if len(self.accepted_decision_refs) != len(set(self.accepted_decision_refs)):
            raise ProfilingPolicyError("profiling decision references must be unique")

        metrics = frozenset(self.allowed_metrics)
        if not metrics or not metrics.issubset(_SAFE_METRICS):
            raise ProfilingPolicyError(
                "allowed metrics must be a non-empty subset of aggregate-only metrics"
            )
        if "ROW_COUNT" not in metrics:
            raise ProfilingPolicyError("ROW_COUNT is required by the profile evidence contract")
        if len(self.allowed_metrics) != len(metrics):
            raise ProfilingPolicyError("allowed metrics must be unique")
        if self.retain_raw_values:
            raise ProfilingPolicyError("raw-value retention is prohibited by this adapter")
        if self.retain_query_text:
            raise ProfilingPolicyError("generated query text may not be retained")
        if self.profiler_engine != "DQX":
            raise ProfilingPolicyError("the approved profiling engine must be DQX")
        if not _SEMANTIC_VERSION.fullmatch(self.profiler_engine_version):
            raise ProfilingPolicyError("profiler engine version must be semantic X.Y.Z")
        if not self.allow_transient_rich_statistics:
            raise ProfilingPolicyError(
                "standard DQX profiling requires explicit transient rich-statistics authorization"
            )
        if self.persist_generated_rules:
            raise ProfilingPolicyError(
                "DQX-generated rules must remain unpersisted until a governed draft-rule contract exists"
            )

        positive_limits = {
            "max_tables": self.max_tables,
            "max_attributes": self.max_attributes,
            "max_queries": self.max_queries,
            "per_query_timeout_seconds": self.per_query_timeout_seconds,
            "total_timeout_seconds": self.total_timeout_seconds,
            "max_concurrency": self.max_concurrency,
            "evidence_retention_days": self.evidence_retention_days,
        }
        invalid = sorted(name for name, value in positive_limits.items() if value <= 0)
        if invalid:
            raise ProfilingPolicyError(f"positive policy limits are required: {invalid}")
        if self.max_concurrency != 1:
            raise ProfilingPolicyError("the first proof slice requires concurrency of 1")
        if self.total_timeout_seconds < self.per_query_timeout_seconds:
            raise ProfilingPolicyError(
                "total timeout must be at least the per-query timeout"
            )


@dataclass(frozen=True)
class AggregateProfilePlan:
    """Ephemeral query plan; only ``query_ref`` is suitable for persistence."""

    query_ref: str
    query_text: str
    template_version: str
    metric_aliases: tuple[tuple[str, str, str], ...]


def _quote_identifier(identifier: str) -> str:
    if not _SAFE_IDENTIFIER.fullmatch(identifier):
        raise ProfilingPolicyError(f"unsafe source identifier: {identifier!r}")
    return f"`{identifier}`"


def build_aggregate_profile_plan(
    *,
    catalog: str,
    schema: str,
    table: str,
    attributes: tuple[str, ...],
    requested_table_count: int,
    requested_attribute_count: int,
    policy: ProfilingPolicy,
) -> AggregateProfilePlan:
    """Build one bounded SELECT containing counts only and no source values."""

    policy.validate_for_execution()
    if requested_table_count <= 0 or requested_table_count > policy.max_tables:
        raise ProfilingPolicyError("requested table count exceeds the approved budget")
    if not attributes:
        raise ProfilingPolicyError("at least one attribute is required")
    if (
        requested_attribute_count <= 0
        or requested_attribute_count > policy.max_attributes
        or len(attributes) > requested_attribute_count
    ):
        raise ProfilingPolicyError("requested attribute count exceeds the approved budget")
    if len(attributes) != len(set(attributes)):
        raise ProfilingPolicyError("profile attributes must be unique")
    if requested_table_count > policy.max_queries:
        raise ProfilingPolicyError("requested query count exceeds the approved budget")

    qualified = ".".join(
        _quote_identifier(identifier) for identifier in (catalog, schema, table)
    )
    expressions = ["count(*) AS `row_count`"]
    aliases: list[tuple[str, str, str]] = []
    for ordinal, attribute in enumerate(attributes):
        quoted = _quote_identifier(attribute)
        if "NULL_COUNT" in policy.allowed_metrics:
            alias = f"c{ordinal:04d}_null_count"
            expressions.append(f"count_if({quoted} IS NULL) AS `{alias}`")
            aliases.append((alias, attribute, "NULL_COUNT"))
        if "DISTINCT_COUNT" in policy.allowed_metrics:
            alias = f"c{ordinal:04d}_distinct_count"
            expressions.append(f"count(DISTINCT {quoted}) AS `{alias}`")
            aliases.append((alias, attribute, "DISTINCT_COUNT"))

    query_text = "SELECT\n  " + ",\n  ".join(expressions) + f"\nFROM {qualified}"
    canonical = json.dumps(
        {
            "template_version": _TEMPLATE_VERSION,
            "policy_id": policy.policy_id,
            "policy_version": policy.policy_version,
            "catalog": catalog,
            "schema": schema,
            "table": table,
            "attributes": attributes,
            "metrics": policy.allowed_metrics,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    query_ref = "profile_query_" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
    return AggregateProfilePlan(
        query_ref=query_ref,
        query_text=query_text,
        template_version=_TEMPLATE_VERSION,
        metric_aliases=tuple(aliases),
    )
