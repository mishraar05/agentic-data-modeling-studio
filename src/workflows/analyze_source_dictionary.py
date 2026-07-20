# Databricks notebook source
# MAGIC %md
# MAGIC # Analyze source dictionary (Phases 3-5)
# MAGIC
# MAGIC Runs the Source Data Analyst over the metadata evidence captured by
# MAGIC `snapshot_source_metadata`, using two Databricks Foundation Model endpoints
# MAGIC (producer + an independent critic). Writes DRAFT dictionary objects and
# MAGIC attributes, open questions, critic findings, and human review items. Nothing
# MAGIC is auto-approved.
# MAGIC
# MAGIC NOTE: runtime notebook — validated on Databricks (Spark + Unity Catalog +
# MAGIC serving endpoints), not in offline unit tests.

# COMMAND ----------

# DBTITLE 1,Load configuration and analyze source
import sys
from pathlib import PurePosixPath

from pyspark.sql import functions as F


def _add_bundle_source_to_python_path() -> None:
    ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
    root = PurePosixPath(ctx.notebookPath().get()).parents[1]
    if not root.as_posix().startswith("/Workspace/"):
        root = PurePosixPath("/Workspace") / root.as_posix().lstrip("/")
    if root.as_posix() not in sys.path:
        sys.path.insert(0, root.as_posix())


_add_bundle_source_to_python_path()

from agentic_data_modeler.analyst import analyze_source
from agentic_data_modeler.analyst.model import DatabricksFoundationModel
from agentic_data_modeler.config.job_params import resolve_job_params
from agentic_data_modeler.knowledge.registry import select_approved_pack
from agentic_data_modeler.slice.context import _load_glossary
from agentic_data_modeler.slice.records import Scope

# Create widgets for dynamic parameters
DYNAMIC = ("context_snapshot_id", "source_snapshot_id")
for w in ("run_id", *DYNAMIC):
    dbutils.widgets.text(w, "")

# Derive REPO_ROOT as bundle root (parent of src/) with /Workspace prefix
REPO_ROOT_RAW = str(Path(sys.path[0]).parent)
if not REPO_ROOT_RAW.startswith("/Workspace/"):
    REPO_ROOT = "/Workspace" + REPO_ROOT_RAW
else:
    REPO_ROOT = REPO_ROOT_RAW
params = resolve_job_params(dbutils, REPO_ROOT, dynamic_keys=("run_id", *DYNAMIC))

# Extract endpoints from metadata
producer_endpoint = params["models"]["producer_endpoint"]
critic_endpoint   = params["models"]["critic_endpoint"]

# Critic independence check (ADR-005 F1) - PROTECTED guard + mandatory requirement
if not critic_endpoint or critic_endpoint == producer_endpoint:
    raise ValueError("Independent critic is mandatory: set a distinct models.critic_endpoint.")

producer = DatabricksFoundationModel(producer_endpoint)
critic   = DatabricksFoundationModel(critic_endpoint)   # never None in this pipeline

# Build run parameters
run_id = params["run_id"]
context_snapshot_id = params["context_snapshot_id"]
source_snapshot_id = params["source_snapshot_id"]

print(f"✅ Config loaded: {params['source']['catalog']}.{params['source']['schema']}")
print(f"   Pack: {params['pack']['id']}@{params['pack']['version']}")
print(f"   Producer: {producer_endpoint}")
print(f"   Critic: {critic_endpoint}")


def _q(*idents: str) -> str:
    return ".".join(f"`{i}`" for i in idents)


def _rows(table: str, ref_col: str, ref_val: str) -> list[dict]:
    t = _q(params["output"]["catalog"], params["output"]["schema"], table)
    return [r.asDict(recursive=True) for r in
            spark.table(t).where(F.col(ref_col) == ref_val).collect()]


# --- assemble the governed glossary from the approved pack (semantic context) ---
manifest = select_approved_pack(
    __import__("pathlib").Path(REPO_ROOT), 
    pack_id=params["pack"]["id"], 
    pack_version=params["pack"]["version"],
    geography=params["pack"]["geography"], 
    lob=params["lob"], 
    domains=set(filter(None, params["pack"]["domains"].split(","))))
glossary = _load_glossary(__import__("pathlib").Path(REPO_ROOT), manifest)

# --- read Phase-1 evidence for this snapshot ---
object_observations = _rows("source_object_observation", "source_snapshot_ref", source_snapshot_id)
attribute_observations = _rows("source_attribute_observation", "source_snapshot_ref", source_snapshot_id)

scope = Scope(
    lob=params["lob"], 
    domain=params["domain"], 
    run_id=run_id,
    memory_partition=f"{params['source']['catalog']}.{params['source']['schema']}")

# --- episodic read: prior dictionary for this source (approved + prior AI drafts), excluding this run ---
from agentic_data_modeler.analyst.episodic import build_prior

prior_rows = [
    r.asDict(recursive=True) for r in
    spark.table(_q(params["output"]["catalog"], params["output"]["schema"], "source_dictionary_attribute"))
    .where((F.col("lob") == params["lob"]) & (F.col("domain") == params["domain"])
           & (F.col("provenance.run_id") != run_id))
    .collect()
]
prior = build_prior(prior_rows, memory_partition=f"{params['source']['catalog']}.{params['source']['schema']}")

# Initialize models (critic independence already validated above)
draft = analyze_source(
    REPO_ROOT, scope, context_snapshot_ref=context_snapshot_id,
    object_observations=object_observations, attribute_observations=attribute_observations,
    producer_model=producer, critic_model=critic, glossary=glossary, prior=prior)

# COMMAND ----------


def _merge(table: str, records: list[dict]) -> None:
    if not records:
        return
    target = _q(params["output"]["catalog"], params["output"]["schema"], table)
    df = spark.createDataFrame(records, schema=spark.table(target).schema)
    df.createOrReplaceTempView(f"_stage_{table}")
    spark.sql(f"""
        MERGE INTO {target} AS t USING _stage_{table} AS s
        ON t.record_id = s.record_id
        WHEN NOT MATCHED THEN INSERT *
    """)


_merge("source_dictionary_object", draft.dictionary_objects)
_merge("source_dictionary_attribute", draft.dictionary_attributes)
_merge("source_dictionary_code_value", draft.code_values)
_merge("open_question", draft.open_questions)
_merge("validation_finding", draft.validation_findings)
_merge("review_item", draft.review_items)

print("Source dictionary drafted (DRAFT — pending human review)")
for k, v in draft.stats.items():
    print(f"  {k}={v}")