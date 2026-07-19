# First real SDD run — runbook + scoring sheet

Turns "deployed" into "proven": run the Source Data Dictionary agent once on real
`gw_pc_bronze` tables, review the drafts, and score a handful against answers you
already know (the Charter §7 evaluation gate).

## 0. Prerequisites (confirm before running)

- Bundle deployed to the workspace (`databricks bundle deploy -t dev`).
- Knowledge pack `public_us_pnc_personal_auto@0.6.0` is `APPROVED` + `runtime_eligible` (it is).
- Control (output) tables exist in `insurance_source_discovery.control` (the 30-odd contract tables).
- Real source tables exist in `insurance_source_discovery.gw_pc_bronze`.
- **Two different** Foundation Model serving endpoints are reachable (producer + critic).
  They MUST differ — the job now fails fast if they are equal.

## 1. Variables to set (via target override or `--var`)

| Variable | Value |
|---|---|
| `source_catalog` | `insurance_source_discovery` |
| `source_schema` | `gw_pc_bronze` |
| `source_scope_mode` | `SCHEMA_ALL_TABLES` (every table) |
| `run_mode` | `METADATA_ONLY` (facts only, no row values) |
| `source_access_granted` | `true` |
| `producer_endpoint` | your serving endpoint, e.g. `databricks-meta-llama-3-3-70b-instruct` |
| `critic_endpoint` | a **different** endpoint |
| identities | `execution_principal`, `workspace_host`, `authorization_ref`, `registration_mode`, `client_name` |

## 2. Run order

Run these jobs/tasks in order (find exact job keys in `resources/*.job.yml`, then
`databricks bundle run -t dev <job_key>`):

1. **`source_discovery`** — validate scope → discover tables → register work package →
   **snapshot metadata** → profile → assemble evidence. Produces `source_snapshot`,
   `source_object_observation`, `source_attribute_observation`.
2. **`assemble_context`** — pins the pack slice + evidence set → writes `context_snapshot`.
   Note its `context_snapshot_id` output.
3. **`analyze_source_dictionary`** — the AI agent. Pass `source_snapshot_id` and
   `context_snapshot_id` from the steps above, plus the two endpoints. Writes DRAFT
   dictionary objects/attributes, open questions, critic findings, review items.

## 3. What to watch (first-run failure modes)

- **The first Delta write** in `analyze_source_dictionary` (nested structs → Delta).
  If anything fails, it fails here. Check the MERGE step error, not the model.
- **`COVERAGE` findings with severity `BLOCKING`** in `validation_finding` → a column
  slipped through without a record. Should be zero.
- **Critic actually ran on a different endpoint** (else `critic_agreement=CONFIRMED`
  is self-agreement).

## 4. Look at the output (SQL)

```sql
-- how the run turned out
SELECT lifecycle_state, business_name.evidence_state AS name_state, COUNT(*)
FROM insurance_source_discovery.control.source_dictionary_attribute
GROUP BY 1,2;

-- what needs a human (privacy, unresolved, contradictions)
SELECT question_type, question_text FROM insurance_source_discovery.control.open_question;
SELECT severity, finding_type, finding_text FROM insurance_source_discovery.control.validation_finding;
```

Optionally generate the Excel: call `build_source_dictionary_workbook` over the
observation tables (add `openpyxl` to that task's environment first).

## 5. Human review

Everything is `DRAFT` — nothing auto-approved. A reviewer works the `review_item`
queue: approve / modify / reject / defer. Confirm the privacy-flagged columns
(e.g. SSN, DOB, names) were all routed to a steward.

## 6. Scoring sheet (prove quality)

Pick **~15 columns you already know the meaning of** (a mix: obvious ones, a couple
of cryptic ones, a coded one, a privacy one). For each, copy what the agent produced
and grade it. Paste this table into Excel:

| Object.Column | Agent business name | Agent definition | Trust state (INFERRED/DECIDED/UNRESOLVED) | Grade (Correct / Partly / Wrong / Rightly-Unresolved) | Notes |
|---|---|---|---|---|---|
| policy.wrtn_prem_amt | | | | | |
| claim.clmnt_ssn | | | | | |
| policy.col_9 | | | | | |
| … (15 rows) | | | | | |

**How to read it:**

- **Accuracy** = (Correct + ½·Partly) ÷ (rows that were resolved). Target ≥ 80%.
- **Safe-abstention** = opaque/ambiguous columns that were `UNRESOLVED` instead of
  guessed. Those are *good* — count them as wins, not misses.
- **Fabrication rate** = INFERRED claims that are Wrong. By design these still cite
  evidence; if the *evidence-backed* meaning is wrong, that's a prompt/glossary issue.
- **Privacy recall** = did every truly-sensitive column get flagged? Target 100%
  (false negatives are the costly error).

**Verdict:**

- ≥80% accuracy, 100% privacy recall, 0 blocking coverage gaps → **the SDD is proven**;
  promote from dev, and start feeding approved decisions back (the memory loop).
- Lower accuracy → the fix is usually the **prompt** or the **glossary the pack feeds**,
  not the agent code. Adjust and re-run; the guardrails already prevent unsafe output.

Keep the filled sheet as the evaluation evidence Charter §7 asks for.
