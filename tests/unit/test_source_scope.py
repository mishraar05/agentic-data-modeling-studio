import pytest

from agentic_data_modeler.control import (
    SourceObjectCandidate,
    SourceScopeError,
    SourceScopeMode,
    resolve_source_manifest,
)


VISIBLE = (
    SourceObjectCandidate("pc_policy", "TABLE"),
    SourceObjectCandidate("pc_vehicle", "TABLE"),
    SourceObjectCandidate("pc_driver", "TABLE"),
    SourceObjectCandidate("policy_summary", "VIEW"),
    SourceObjectCandidate("pc_policy_backup", "TABLE"),
)


def test_schema_all_discovers_every_eligible_table_and_freezes_sort_order() -> None:
    manifest = resolve_source_manifest(
        catalog="insurance",
        schema="policycenter",
        scope_mode=SourceScopeMode.SCHEMA_ALL_TABLES,
        visible_objects=reversed(VISIBLE),
        explicit_tables=(),
        include_patterns=("*",),
        exclude_patterns=(),
        object_types=("TABLE",),
    )
    assert manifest.tables == (
        "pc_driver",
        "pc_policy",
        "pc_policy_backup",
        "pc_vehicle",
    )
    assert len(manifest.fingerprint()) == 64


def test_pattern_scope_applies_governed_includes_and_excludes() -> None:
    manifest = resolve_source_manifest(
        catalog="insurance",
        schema="policycenter",
        scope_mode=SourceScopeMode.PATTERN_BASED,
        visible_objects=VISIBLE,
        explicit_tables=(),
        include_patterns=("pc_*",),
        exclude_patterns=("*_backup",),
        object_types=("TABLE",),
    )
    assert manifest.tables == ("pc_driver", "pc_policy", "pc_vehicle")


def test_explicit_scope_proves_every_requested_table_is_visible() -> None:
    with pytest.raises(SourceScopeError, match="not visible or eligible"):
        resolve_source_manifest(
            catalog="insurance",
            schema="policycenter",
            scope_mode=SourceScopeMode.EXPLICIT_TABLES,
            visible_objects=VISIBLE,
            explicit_tables=("missing_table",),
            include_patterns=(),
            exclude_patterns=(),
            object_types=("TABLE",),
        )


def test_schema_scope_fails_instead_of_silently_skipping_unsupported_names() -> None:
    with pytest.raises(SourceScopeError, match="unsupported by the current contract"):
        resolve_source_manifest(
            catalog="insurance",
            schema="policycenter",
            scope_mode=SourceScopeMode.SCHEMA_ALL_TABLES,
            visible_objects=(SourceObjectCandidate("table with spaces", "TABLE"),),
            explicit_tables=(),
            include_patterns=("*",),
            exclude_patterns=(),
            object_types=("TABLE",),
        )


def test_scope_resolving_to_zero_tables_fails_closed() -> None:
    with pytest.raises(SourceScopeError, match="zero eligible tables"):
        resolve_source_manifest(
            catalog="insurance",
            schema="policycenter",
            scope_mode=SourceScopeMode.PATTERN_BASED,
            visible_objects=VISIBLE,
            explicit_tables=(),
            include_patterns=("claim_*",),
            exclude_patterns=(),
            object_types=("TABLE",),
        )
