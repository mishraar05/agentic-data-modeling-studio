import pytest

from agentic_data_modeler.evidence import (
    ColumnMetadata,
    ConstraintMetadata,
    MetadataInventory,
    MetadataInventoryError,
    ObjectMetadata,
    one_based_ordinal_offset,
    stable_record_id,
)


def _inventory(*, expected_tables=("pc_policy", "pc_policy_period")) -> MetadataInventory:
    return MetadataInventory.from_iterables(
        catalog="insurance_source_discovery",
        schema="gw_pc_bronze",
        expected_tables=expected_tables,
        objects=(
            ObjectMetadata(
                name="pc_policy_period",
                object_type="TABLE",
                columns=(
                    ColumnMetadata("period_id", 1, "BIGINT", False, constraint_types=("PRIMARY KEY",)),
                    ColumnMetadata("policy_id", 2, "BIGINT", False, constraint_types=("FOREIGN KEY",)),
                ),
                constraints=(ConstraintMetadata("period_pk", "PRIMARY KEY", ("period_id",)),),
            ),
            ObjectMetadata(
                name="pc_policy",
                object_type="TABLE",
                columns=(ColumnMetadata("policy_id", 1, "BIGINT", False),),
            ),
        ),
    )


def test_inventory_reconciles_counts_and_stable_fingerprint() -> None:
    first = _inventory()
    reordered = MetadataInventory.from_iterables(
        catalog=first.catalog,
        schema=first.schema,
        expected_tables=reversed(first.expected_tables),
        objects=reversed(first.objects),
    )
    assert first.table_count == 2
    assert first.column_count == 3
    assert first.fingerprint() == reordered.fingerprint()
    assert first.snapshot_id("run-metadata-test") == reordered.snapshot_id("run-metadata-test")


def test_missing_allow_list_object_fails_coverage_gate() -> None:
    inventory = _inventory(expected_tables=("pc_policy", "pc_policy_period", "pc_vehicle"))
    with pytest.raises(MetadataInventoryError, match=r"missing=\['pc_vehicle'\]"):
        inventory.validate()


def test_duplicate_column_or_invalid_ordinal_fails() -> None:
    inventory = MetadataInventory.from_iterables(
        catalog="catalog",
        schema="schema",
        expected_tables=("table_a",),
        objects=(
            ObjectMetadata(
                "table_a",
                "TABLE",
                (
                    ColumnMetadata("id", 1, "BIGINT", False),
                    ColumnMetadata("id", 2, "BIGINT", False),
                ),
            ),
        ),
    )
    with pytest.raises(MetadataInventoryError, match="duplicate columns"):
        inventory.validate()


def test_constraint_role_uses_deterministic_priority() -> None:
    column = ColumnMetadata(
        "id",
        1,
        "BIGINT",
        False,
        constraint_types=("CHECK", "PRIMARY KEY", "UNIQUE"),
    )
    assert column.constraint_role() == "PRIMARY_KEY"


def test_constraint_cannot_reference_unknown_column() -> None:
    inventory = MetadataInventory.from_iterables(
        catalog="catalog",
        schema="schema",
        expected_tables=("table_a",),
        objects=(
            ObjectMetadata(
                "table_a",
                "TABLE",
                (ColumnMetadata("id", 1, "BIGINT", False),),
                (ConstraintMetadata("bad_fk", "FOREIGN KEY", ("missing_id",)),),
            ),
        ),
    )
    with pytest.raises(MetadataInventoryError, match="unknown columns"):
        inventory.validate()


def test_stable_record_id_does_not_expose_physical_names() -> None:
    record_id = stable_record_id("source_attribute", "run-metadata-test", "pc_policy", "policy_id")
    assert record_id.startswith("source_attribute_")
    assert "pc_policy" not in record_id


def test_zero_based_platform_ordinals_are_normalized_to_contract_positions() -> None:
    assert one_based_ordinal_offset((0, 1, 2)) == 1
    assert one_based_ordinal_offset((1, 2, 3)) == 0


def test_duplicate_or_negative_platform_ordinals_fail() -> None:
    with pytest.raises(MetadataInventoryError, match="invalid ordinal"):
        one_based_ordinal_offset((0, 0))
    with pytest.raises(MetadataInventoryError, match="invalid ordinal"):
        one_based_ordinal_offset((-1, 0))
