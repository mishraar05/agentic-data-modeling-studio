# Databricks notebook source
# MAGIC %md
# MAGIC # Assemble governed context
# MAGIC
# MAGIC Pins the exact evidence set and approved knowledge-pack slice used by the
# MAGIC semantic agents. Execution identity is the solution run; no engagement or
# MAGIC work-package identifier is part of the context contract.

# COMMAND ----------

import sys
from pathlib import Path, PurePosixPath

from pyspark.sql import functions as F


def _bundle_paths() -> tuple[PurePosixPath, PurePosixPath]:
    ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    root = PurePosixPath(ctx.notebookPath().get()).parents[1]
    if not root.as_posix().startswith("/Workspace/"):
        root = PurePosixPath("/Workspace") / root.as_posix().lstrip("/")
    if root.as_posix() not in sys.path:
        sys.path.insert(0, root.as_posix())
    return root, root.parent


_, BUNDLE_ROOT = _bundle_paths()

from agentic_data_modeler.knowledge.registry import select_approved_pack
from agentic_data_modeler.slice.context import assemble_context
from agentic_data_modeler.slice.records import Scope


PARAMS = (
    "run_id", "lob", "domain", "output_catalog", "output_schema",
    "pack_id", "pack_version", "geography", "pack_domains",
)
for name in PARAMS:
    dbutils.widgets.text(name, "")
args = {name: dbutils.widgets.get(name).strip() for name in PARAMS}
missing = [name for name in PARAMS if not args[name]]
if missing:
    raise ValueError(f"Missing governed context parameters: {missing}")


def _q(table: str) -> str:
    return ".".join(f"`{v}`" for v in (args["output_catalog"], args["output_schema"], table))


run_rows = spark.table(_q("solution_run")).where(F.col("record_id") == args["run_id"]).collect()
if len(run_rows) != 1:
    raise ValueError(f"Expected one solution run; found {len(run_rows)}")
run = run_rows[0].asDict(recursive=True)
if run["workflow_state"] not in {"EVIDENCE_READY", "CONTEXT_READY"}:
    raise ValueError(f"Context assembly is not allowed from {run['workflow_state']}")
if (run["lob"], run["domain"]) != (args["lob"], args["domain"]):
    raise ValueError("Requested LOB/domain differs from the registered solution run")

evidence_rows = (
    spark.table(_q("evidence_set"))
    .where(F.col("solution_run_ref") == args["run_id"])
    .orderBy(F.col("assembly_timestamp").desc())
    .limit(1)
    .collect()
)
if len(evidence_rows) != 1:
    raise ValueError("A committed evidence set is required before context assembly")
evidence = evidence_rows[0].asDict(recursive=True)
if evidence["source_snapshot_ref"] is None:
    raise ValueError("Evidence set does not pin a source snapshot")

repo_root = Path(BUNDLE_ROOT.as_posix())
manifest = select_approved_pack(
    repo_root,
    pack_id=args["pack_id"], pack_version=args["pack_version"],
    geography=args["geography"], lob=args["lob"],
    domains=set(filter(None, args["pack_domains"].split(","))),
)
scope = Scope(lob=args["lob"], domain=args["domain"], run_id=args["run_id"])
context = assemble_context(
    repo_root, scope, manifest=manifest,
    evidence_set_ref=evidence["record_id"], evidence_fingerprint=evidence["fingerprint"],
)

target = _q("context_snapshot")
df = spark.createDataFrame([context.snapshot], schema=spark.table(target).schema)
df.createOrReplaceTempView("_context_snapshot_stage")
spark.sql(f"""
    MERGE INTO {target} t USING _context_snapshot_stage s ON t.record_id = s.record_id
    WHEN NOT MATCHED THEN INSERT *
""")
spark.sql(f"""
    UPDATE {_q('solution_run')}
    SET workflow_state='CONTEXT_READY', updated_at=current_timestamp(),
        knowledge_pack_id='{args['pack_id']}', knowledge_pack_version='{args['pack_version']}'
    WHERE record_id='{args['run_id']}' AND workflow_state IN ('EVIDENCE_READY','CONTEXT_READY')
""")

dbutils.jobs.taskValues.set(key="context_snapshot_id", value=context.snapshot_id)
dbutils.jobs.taskValues.set(key="evidence_set_id", value=evidence["record_id"])
dbutils.jobs.taskValues.set(key="source_snapshot_id", value=evidence["source_snapshot_ref"])
print(f"context_snapshot_id={context.snapshot_id}")
