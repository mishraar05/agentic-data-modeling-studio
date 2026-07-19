#!/usr/bin/env python3
"""
Migration Script: Move Contract Tables from Bronze Schemas to Control Schema
Version: 1.0.0
Purpose: Migrate 29 contract tables from gw_*_bronze schemas to control schema
"""

from pyspark.sql import SparkSession

# Initialize Spark
spark = SparkSession.builder.getOrCreate()

# Configuration
CATALOG = "insurance_source_discovery"
SOURCE_SCHEMAS = ["gw_pc_bronze", "gw_cc_bronze", "gw_bc_bronze"]
TARGET_SCHEMA = "control"

# List of all 29 contract tables
CONTRACT_TABLES = [
    "solution_run",
    "artifact_version",
    "source_snapshot",
    "context_snapshot",
    "profile_snapshot",
    "document_set",
    "requirement_set",
    "evidence_set",
    "evidence_item",
    "source_object_observation",
    "source_attribute_observation",
    "profile_evidence",
    "relationship_candidate",
    "analytical_requirement",
    "reporting_requirement",
    "business_term",
    "business_rule",
    "source_dictionary_object",
    "source_dictionary_attribute",
    "source_dictionary_relationship",
    "source_dictionary_code_value",
    "validation_finding",
    "review_item",
    "review_decision",
    "open_question",
    "artifact_dependency",
    "lineage_edge",
    "source_dictionary_handoff",
    "skill_resolution",
]


def migrate_table(table_name: str, source_schema: str, target_schema: str) -> dict:
    """
    Migrate a single table from source schema to target schema.
    
    Returns: dict with migration status
    """
    source_table = f"{CATALOG}.{source_schema}.{table_name}"
    target_table = f"{CATALOG}.{target_schema}.{table_name}"
    
    result = {
        "table": table_name,
        "source": source_schema,
        "status": "unknown",
        "row_count": 0,
        "error": None
    }
    
    try:
        # Check if source table exists
        source_df = spark.table(source_table)
        row_count = source_df.count()
        result["row_count"] = row_count
        
        print(f"  📋 {table_name}: Found {row_count} rows in {source_schema}")
        
        # Create or replace table in control schema
        if row_count > 0:
            print(f"     → Copying {row_count} rows to {target_schema}")
            source_df.write.mode("append").saveAsTable(target_table)
            result["status"] = "migrated"
        else:
            print(f"     → No data to migrate (empty table)")
            result["status"] = "empty"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"  ❌ Error migrating {table_name}: {e}")
    
    return result


def drop_table(table_name: str, schema: str) -> dict:
    """Drop a table from source schema after successful migration."""
    table_path = f"{CATALOG}.{schema}.{table_name}"
    
    result = {
        "table": table_name,
        "schema": schema,
        "status": "unknown",
        "error": None
    }
    
    try:
        spark.sql(f"DROP TABLE IF EXISTS {table_path}")
        result["status"] = "dropped"
        print(f"  🗑️  Dropped {table_name} from {schema}")
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"  ❌ Error dropping {table_name} from {schema}: {e}")
    
    return result


def main():
    """Execute the migration."""
    print("=" * 80)
    print("Contract Tables Migration: Bronze → Control")
    print("=" * 80)
    print()
    
    migration_results = []
    
    # Step 1: Migrate tables from all bronze schemas to control
    print("📦 Phase 1: Migrating tables from bronze schemas to control")
    print()
    
    for source_schema in SOURCE_SCHEMAS:
        print(f"\n▶ Processing {source_schema}:")
        print("-" * 60)
        
        for table_name in CONTRACT_TABLES:
            result = migrate_table(table_name, source_schema, TARGET_SCHEMA)
            migration_results.append(result)
    
    # Step 2: Drop tables from bronze schemas
    print("\n\n🗑️  Phase 2: Removing tables from bronze schemas")
    print()
    
    drop_results = []
    
    for source_schema in SOURCE_SCHEMAS:
        print(f"\n▶ Cleaning up {source_schema}:")
        print("-" * 60)
        
        for table_name in CONTRACT_TABLES:
            result = drop_table(table_name, source_schema)
            drop_results.append(result)
    
    # Summary
    print("\n\n" + "=" * 80)
    print("Migration Summary")
    print("=" * 80)
    
    # Migration stats
    migrated = sum(1 for r in migration_results if r["status"] == "migrated")
    empty = sum(1 for r in migration_results if r["status"] == "empty")
    errors = sum(1 for r in migration_results if r["status"] == "error")
    total_rows = sum(r["row_count"] for r in migration_results)
    
    print(f"\n📊 Migration Results:")
    print(f"   - Tables migrated: {migrated}")
    print(f"   - Empty tables: {empty}")
    print(f"   - Errors: {errors}")
    print(f"   - Total rows migrated: {total_rows:,}")
    
    # Drop stats
    dropped = sum(1 for r in drop_results if r["status"] == "dropped")
    drop_errors = sum(1 for r in drop_results if r["status"] == "error")
    
    print(f"\n🗑️  Cleanup Results:")
    print(f"   - Tables dropped: {dropped}")
    print(f"   - Errors: {drop_errors}")
    
    if errors > 0 or drop_errors > 0:
        print("\n⚠️  Some operations failed. Check logs above for details.")
    else:
        print("\n✅ Migration completed successfully!")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
