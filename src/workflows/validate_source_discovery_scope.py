# Databricks notebook source
# MAGIC %md
# MAGIC # Validate source-discovery work-package scope
# MAGIC
# MAGIC This entry point parses per-run job parameters and fails before any
# MAGIC source read when scope, policy, contract version, or output separation
# MAGIC is incomplete or unsafe.

# COMMAND ----------

from agentic_data_modeler.control import RuntimeRequest


PARAMETERS = (
    "run_id",
    "engagement_id",
    "work_package_id",
    "lob",
    "domain",
    "source_catalog",
    "source_schema",
    "source_tables",
    "source_system_id",
    "source_product",
    "source_module",
    "source_version",
    "run_mode",
    "profiling_policy_id",
    "profiling_policy_version",
    "document_set_id",
    "requirement_set_id",
    "output_catalog",
    "output_schema",
    "contract_set_version",
)

for parameter in PARAMETERS:
    dbutils.widgets.text(parameter, "")

request = RuntimeRequest.from_parameters(
    {parameter: dbutils.widgets.get(parameter) for parameter in PARAMETERS}
)

print("Source-discovery scope validation passed")
print(f"run_id={request.run_id}")
print(f"engagement_id={request.engagement_id}")
print(f"work_package_id={request.work_package_id}")
print(f"lob={request.lob}")
print(f"domain={request.domain}")
print(f"source_table_count={len(request.source_tables)}")
print(f"run_mode={request.profiling_mode.value}")
print(f"request_fingerprint={request.fingerprint()}")
