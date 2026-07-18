"""Synthetic Personal Auto source tables (stand-in for a real allow-listed slice).

Includes primary/foreign keys, a privacy-sensitive column, a glossary-matchable
column, and one deliberately opaque column to exercise the UNRESOLVED path.
"""

from __future__ import annotations

from ..evidence.metadata import ColumnMetadata, MetadataInventory, ObjectMetadata


def _col(name, ordinal, data_type, nullable=True, constraint=()):
    return ColumnMetadata(name=name, ordinal_position=ordinal, data_type=data_type,
                          nullable=nullable, constraint_types=tuple(constraint))


def personal_auto_inventory(catalog: str = "insurance_raw", schema: str = "gw_pc") -> MetadataInventory:
    policy = ObjectMetadata(
        name="policy", object_type="TABLE",
        columns=(
            _col("policy_id", 1, "STRING", False, ("PRIMARY_KEY",)),
            _col("policyholder_id", 2, "STRING", False, ("FOREIGN_KEY",)),
            _col("effective_dt", 3, "DATE"),
            _col("expiration_dt", 4, "DATE"),
            _col("premium_amt", 5, "DECIMAL"),
            _col("status_cd", 6, "STRING"),
        ),
    )
    claim = ObjectMetadata(
        name="claim", object_type="TABLE",
        columns=(
            _col("claim_id", 1, "STRING", False, ("PRIMARY_KEY",)),
            _col("policy_id", 2, "STRING", False, ("FOREIGN_KEY",)),
            _col("loss_dt", 3, "DATE"),
            _col("claim_amt", 4, "DECIMAL"),
            _col("driver_ssn", 5, "STRING"),   # privacy-sensitive
            _col("col7", 6, "STRING"),          # opaque -> UNRESOLVED
        ),
    )
    driver = ObjectMetadata(
        name="driver", object_type="TABLE",
        columns=(
            _col("driver_id", 1, "STRING", False, ("PRIMARY_KEY",)),
            _col("first_name", 2, "STRING"),    # privacy-sensitive
            _col("last_name", 3, "STRING"),     # privacy-sensitive
            _col("dob", 4, "DATE"),             # privacy-sensitive
            _col("license_num", 5, "STRING"),
        ),
    )
    return MetadataInventory.from_iterables(
        catalog=catalog, schema=schema,
        expected_tables=("policy", "claim", "driver"),
        objects=(policy, claim, driver),
    )
