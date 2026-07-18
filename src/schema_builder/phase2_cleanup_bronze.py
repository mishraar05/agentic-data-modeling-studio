#!/usr/bin/env python3
"""
Phase 2: Cleanup - Drop Contract Tables from Bronze Schemas
(Run AFTER verifying control schema tables)
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

CATALOG = "insurance_source_discovery"
SOURCE_SCHEMAS = ["gw_pc_bronze", "gw_cc_bronze", "gw_bc_bronze"]

CONTRACT_TABLES = [
    "engagement", "work_package", "solution_run", "artifact_version",
    "source_snapshot", "context_snapshot", "profile_snapshot",
    "document_set", "requirement_set", "evidence_set", "evidence_item",
    "source_object_observation", "source_attribute_observation",
    "profile_evidence", "relationship_candidate", "analytical_requirement",
    "reporting_requirement", "business_term", "business_rule",
    "source_dictionary_object", "source_dictionary_attribute",
    "source_dictionary_relationship", "source_dictionary_code_value",
    "validation_finding", "review_item", "review_decision", "open_question",
    "artifact_dependency", "lineage_edge", "source_dictionary_handoff",
    "skill_resolution",
]

print("=" * 80)
print("⚠️  Phase 2: Cleanup Bronze Schemas (DESTRUCTIVE)")
print("=" * 80)
print()
print("This will DROP all 31 contract tables from:")
print("  - gw_pc_bronze")
print("  - gw_cc_bronze")
print("  - gw_bc_bronze")
print()
response = input("Are you sure you want to proceed? (yes/no): ")

if response.lower() != "yes":
    print("\n❌ Cleanup cancelled.")
    exit(0)

print("\n🗑️  Proceeding with cleanup...")
print()

for source_schema in SOURCE_SCHEMAS:
    print(f"\n▶ Cleaning {source_schema}:")
    print("-" * 60)
    
    for table_name in CONTRACT_TABLES:
        table_path = f"{CATALOG}.{source_schema}.{table_name}"
        try:
            spark.sql(f"DROP TABLE IF EXISTS {table_path}")
            print(f"  ✓ Dropped {table_name}")
        except Exception as e:
            print(f"  ❌ Error dropping {table_name}: {e}")

print("\n✅ Cleanup complete!")
