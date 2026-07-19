#!/usr/bin/env python3
"""
Phase 1: Copy Contract Tables from Bronze Schemas to Control Schema
(Safe - no table drops)
"""

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

CATALOG = "insurance_source_discovery"
SOURCE_SCHEMAS = ["gw_pc_bronze", "gw_cc_bronze", "gw_bc_bronze"]
TARGET_SCHEMA = "control"

CONTRACT_TABLES = [
    "solution_run", "artifact_version",
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
print("Phase 1: Copy Contract Tables to Control Schema (Safe Migration)")
print("=" * 80)
print()

migration_results = []

for source_schema in SOURCE_SCHEMAS:
    print(f"\n▶ Processing {source_schema}:")
    print("-" * 60)
    
    for table_name in CONTRACT_TABLES:
        source_table = f"{CATALOG}.{source_schema}.{table_name}"
        target_table = f"{CATALOG}.{TARGET_SCHEMA}.{table_name}"
        
        try:
            source_df = spark.table(source_table)
            row_count = source_df.count()
            
            print(f"  📋 {table_name}: Found {row_count} rows")
            
            if row_count > 0:
                print(f"     → Copying to {TARGET_SCHEMA}")
                source_df.write.mode("append").saveAsTable(target_table)
                migration_results.append({"table": table_name, "rows": row_count, "status": "success"})
            else:
                print(f"     → Empty table, skipping")
                migration_results.append({"table": table_name, "rows": 0, "status": "empty"})
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            migration_results.append({"table": table_name, "rows": 0, "status": "error", "error": str(e)})

print("\n" + "=" * 80)
print("Migration Summary")
print("=" * 80)
migrated = sum(1 for r in migration_results if r["status"] == "success")
total_rows = sum(r["rows"] for r in migration_results if r["status"] == "success")
print(f"✅ Tables migrated: {migrated}")
print(f"📊 Total rows: {total_rows:,}")
print("\nNOTE: Original tables in bronze schemas are preserved.")
print("Run phase2_cleanup.py after verification to remove them.")
