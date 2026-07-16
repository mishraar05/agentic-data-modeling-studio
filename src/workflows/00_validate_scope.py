# Databricks notebook source
# MAGIC %md
# MAGIC # Validate modeling work-package scope
# MAGIC
# MAGIC This entry point validates configuration only. It does not read source
# MAGIC values, create target models, or provision schemas.

# COMMAND ----------

PARAMETERS = (
    "run_id",
    "engagement_id",
    "lob",
    "domain",
    "source_catalog",
    "source_schema",
    "source_tables",
    "output_catalog",
    "output_schema",
)

for parameter in PARAMETERS:
    dbutils.widgets.text(parameter, "")

scope = {parameter: dbutils.widgets.get(parameter).strip() for parameter in PARAMETERS}

missing = [name for name, value in scope.items() if not value]
placeholders = [
    name for name, value in scope.items() if value.upper().startswith("REQUIRED_")
]

assert not missing, f"Missing required scope parameters: {sorted(missing)}"
assert not placeholders, f"Replace required placeholders: {sorted(placeholders)}"

source_tables = [item.strip() for item in scope["source_tables"].split(",") if item.strip()]
assert source_tables, "source_tables must contain at least one allow-listed table."
assert len(source_tables) == len(set(source_tables)), "source_tables contains duplicates."

for table_name in source_tables:
    assert all(
        character.isalnum() or character == "_" for character in table_name
    ), f"Unsafe source table identifier: {table_name!r}"

print("Modeling scope validation passed")
print(f"run_id={scope['run_id']}")
print(f"engagement_id={scope['engagement_id']}")
print(f"lob={scope['lob']}")
print(f"domain={scope['domain']}")
print(f"source_table_count={len(source_tables)}")
