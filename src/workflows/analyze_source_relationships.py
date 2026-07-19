# Databricks notebook source
# MAGIC %md
# MAGIC # LLM source relationship analyst
# MAGIC
# MAGIC Uses a bounded context snapshot, approved semantic memory, a producer
# MAGIC model, and an independent critic. Model output is DRAFT and contract gated.

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

from agentic_data_modeler.analyst import RelationshipAgent, assemble_relationship_context
from agentic_data_modeler.analyst.model import DatabricksFoundationModel
from agentic_data_modeler.knowledge.registry import select_approved_pack
from agentic_data_modeler.slice.context import _load_glossary
from agentic_data_modeler.slice.records import Scope


PARAMS = (
    "run_id", "lob", "domain", "output_catalog", "output_schema",
    "context_snapshot_id", "source_snapshot_id", "evidence_set_id",
    "pack_id", "pack_version", "geography", "pack_domains",
    "producer_endpoint", "critic_endpoint",
)
for name in PARAMS:
    dbutils.widgets.text(name, "")
args = {name: dbutils.widgets.get(name).strip() for name in PARAMS}
missing = [name for name in PARAMS if not args[name]]
if missing:
    raise ValueError(f"Missing relationship-agent parameters: {missing}")
if args["producer_endpoint"] == args["critic_endpoint"]:
    raise ValueError("Producer and critic endpoints must be different")


def _q(table: str) -> str:
    return ".".join(f"`{v}`" for v in (args["output_catalog"], args["output_schema"], table))


def _rows(table: str, ref_col: str, ref_value: str) -> list[dict]:
    return [row.asDict(recursive=True) for row in
            spark.table(_q(table)).where(F.col(ref_col) == ref_value).collect()]


context_rows = _rows("context_snapshot", "record_id", args["context_snapshot_id"])
if len(context_rows) != 1 or context_rows[0]["solution_run_ref"] != args["run_id"]:
    raise ValueError("Context snapshot does not belong to the solution run")
context_row = context_rows[0]
if context_row["evidence_set_ref"] != args["evidence_set_id"]:
    raise ValueError("Context snapshot does not pin the requested evidence set")
if (context_row["knowledge_pack_id"], context_row["knowledge_pack_version"]) != (
    args["pack_id"], args["pack_version"]
):
    raise ValueError("Context snapshot does not pin the requested knowledge pack")

source_rows = _rows("source_snapshot", "record_id", args["source_snapshot_id"])
if len(source_rows) != 1 or source_rows[0]["solution_run_ref"] != args["run_id"]:
    raise ValueError("Expected one source snapshot")
source = source_rows[0]

evidence_rows = _rows("evidence_set", "record_id", args["evidence_set_id"])
if (
    len(evidence_rows) != 1
    or evidence_rows[0]["solution_run_ref"] != args["run_id"]
    or evidence_rows[0]["source_snapshot_ref"] != args["source_snapshot_id"]
):
    raise ValueError("Evidence set does not match the run and source snapshot")

objects = _rows("source_object_observation", "source_snapshot_ref", args["source_snapshot_id"])
attributes = _rows("source_attribute_observation", "source_snapshot_ref", args["source_snapshot_id"])

profile_snapshots = (
    spark.table(_q("profile_snapshot"))
    .where(F.col("source_snapshot_ref") == args["source_snapshot_id"])
    .orderBy(F.col("profile_timestamp").desc()).limit(1).collect()
)
profiles = [] if not profile_snapshots else _rows(
    "profile_evidence", "profile_snapshot_ref", profile_snapshots[0]["record_id"]
)

manifest = select_approved_pack(
    Path(BUNDLE_ROOT.as_posix()), pack_id=args["pack_id"], pack_version=args["pack_version"],
    geography=args["geography"], lob=args["lob"],
    domains=set(filter(None, args["pack_domains"].split(","))),
)
glossary = _load_glossary(Path(BUNDLE_ROOT.as_posix()), manifest)

# Durable episodic memory is bounded by LOB/domain and the exact source locator.
# Column expressions keep user-supplied scope values out of SQL text.
candidates_df = spark.table(_q("relationship_candidate")).alias("c")
snapshots_df = spark.table(_q("source_snapshot")).alias("s")
approved = (
    candidates_df.join(
        snapshots_df,
        F.col("s.record_id") == F.col("c.source_snapshot_ref"),
    )
    .where(
        (F.col("c.lifecycle_state") == "APPROVED")
        & (F.col("c.lob") == args["lob"])
        & (F.col("c.domain") == args["domain"])
        & (F.col("s.source_catalog") == source["source_catalog"])
        & (F.col("s.source_schema") == source["source_schema"])
    )
    .select("c.*")
    .collect()
)
prior = []
for row in approved:
    item = row.asDict(recursive=True)
    memory = {
        "parent_object": item["parent_object_name"],
        "parent_attributes": item["parent_attributes"],
        "child_object": item["child_object_name"],
        "child_attributes": item["child_attributes"],
        "relationship_type": item["relationship_type"],
        "relationship_name": item["relationship_name"].get("value"),
        "cardinality": item["cardinality"].get("value"),
        "optionality": item["optionality"].get("value"),
        "review_decision_ref": item["review_decision_ref"],
        "evidence_refs": item["evidence_refs"],
    }
    if all(memory.get(key) for key in (
        "relationship_name", "cardinality", "optionality", "review_decision_ref"
    )):
        prior.append(memory)

relationship_context = assemble_relationship_context(
    lob=args["lob"], domain=args["domain"],
    source_snapshot_ref=args["source_snapshot_id"],
    evidence_set_ref=args["evidence_set_id"],
    context_snapshot_ref=args["context_snapshot_id"],
    object_observations=objects, attribute_observations=attributes,
    profile_evidence=profiles, glossary=glossary, prior_decisions=prior,
)
scope = Scope(
    lob=args["lob"], domain=args["domain"], run_id=args["run_id"],
    memory_partition=f"{source['source_catalog']}.{source['source_schema']}",
)
draft = RelationshipAgent(
    Path(BUNDLE_ROOT.as_posix()), DatabricksFoundationModel(args["producer_endpoint"]),
    DatabricksFoundationModel(args["critic_endpoint"]),
).analyze(scope, relationship_context)


def _merge(table: str, records: list[dict]) -> None:
    if not records:
        return
    target = _q(table)
    df = spark.createDataFrame(records, schema=spark.table(target).schema)
    df.createOrReplaceTempView(f"_stage_{table}")
    spark.sql(f"""
        MERGE INTO {target} t USING _stage_{table} s ON t.record_id = s.record_id
        WHEN NOT MATCHED THEN INSERT *
    """)


_merge("relationship_candidate", draft.candidates)
_merge("open_question", draft.open_questions)
_merge("validation_finding", draft.validation_findings)
_merge("review_item", draft.review_items)

dbutils.jobs.taskValues.set(key="relationship_candidate_count", value=str(len(draft.candidates)))
for key, value in draft.stats.items():
    print(f"{key}={value}")
