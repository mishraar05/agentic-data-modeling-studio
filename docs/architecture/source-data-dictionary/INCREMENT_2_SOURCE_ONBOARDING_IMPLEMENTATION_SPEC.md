# Increment 2 — Source Onboarding Implementation Specification

**Status:** Draft implementation specification for human and architecture review  
**Builder:** Genie Code  
**Planning authority:** Claude/Codex  
**Human authority:** source access, proof-slice, privacy/profiling, retention and acceptance decisions  
**Governing requirements:** `docs/requirements/REQUIREMENTS_CHARTER.md`  
**Controlling design:** `SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md` §§6, 11–13, 17–19  
**Contract dependency:** Increment-1 contracts; this document does not redefine their fields

## 1. Outcome and anti-drift gate

Increment 2 reproducibly moves one authorized work package from `VALIDATED` to `EVIDENCE_READY` by:

1. registering the immutable source and policy boundary;
2. capturing a complete metadata snapshot for every allow-listed object;
3. executing only policy-approved profiling templates;
4. normalizing supplied documents, reports and requirements as cited evidence; and
5. persisting contract-valid evidence and an explicit readiness result.

It advances the Reconstructed Source Data Dictionary by supplying source-dependent facts that the reusable knowledge pack cannot contain. It is reusable across LOBs and domains. It does not infer business meaning, create dictionary definitions, approve artifacts, modify governed knowledge, or create Silver, Gold or STTM artifacts.

## 2. Preconditions

Genie Code must stop before implementation where a required Increment-1 contract is absent or ambiguous. It must consume, not redesign, the approved schemas for:

- `engagement`, `work_package`, `solution_run` and `artifact_version`;
- `source_object_observation`, `source_attribute_observation`, `profile_evidence`, `relationship_candidate` and `evidence_item`;
- `validation_finding` and `open_question`; and
- any evidence-set or snapshot manifest selected by Increment 1.

The following human decisions must be recorded before the indicated gate:

| Decision | Required before | Fail-closed behavior when missing |
|---|---|---|
| Exact proof-slice catalog, schema and table allow-list | metadata execution | do not query the source |
| Execution identity and source/output privileges | metadata execution | authorization finding; stop |
| Profiling mode, sampling, query and time budgets | profiling execution | remain `METADATA_ONLY` or stop, as explicitly decided |
| Sensitive/raw-value, suppression and retention policy | profiling execution | prohibit raw or distributed values |
| Approved document locations, entitlements and extraction policy | evidence normalization | exclude the document and record a finding |
| Quantitative readiness thresholds | `EVIDENCE_READY` transition | do not advance state |

The decision IDs and owners are maintained in `INCREMENT_2_3_HUMAN_DECISION_REGISTER.md`.

## 3. Runtime parameter model

Per-run scope must be Lakeflow **job parameters**, not only bundle variables. Bundle variables remain deployment-time defaults for environment infrastructure such as warehouse/cluster IDs, output catalog defaults and policy registry locations. The job must expose at least:

- `engagement_id`, `work_package_id`, `lob`, `domain`;
- `source_catalog`, `source_schema`, `source_tables` as a JSON array;
- `source_system_id` and optional declared product/module/version;
- `run_mode`;
- `profiling_policy_id` and `profiling_policy_version`;
- `document_set_id` and `requirement_set_id`, when supplied;
- `output_catalog`, `output_schema`; and
- exact Increment-1 contract-set version.

No credential, token, personal data or raw source value may be a bundle variable or job parameter.

## 4. Durable task graph

```text
validate_scope
  -> register_work_package
  -> snapshot_source_metadata
  -> profile_source
  -> normalize_supplied_evidence
  -> verify_evidence_ready
```

| Task | Execution | Authoritative output | Completion gate |
|---|---|---|---|
| `validate_scope` | deterministic | validated run request or findings | no placeholder, unsafe identifier, duplicate object or cross-scope target |
| `register_work_package` | deterministic + authorization lookup | immutable work-package boundary and authorization snapshot | exact principal, purpose, source boundary, output boundary and policy versions authorized |
| `snapshot_source_metadata` | deterministic adapter | object/attribute observations, constraint/index/view observations, metadata snapshot manifest | every allow-listed object captured or explicitly failed |
| `profile_source` | deterministic adapter | profile evidence and profile snapshot manifest | every query template, budget and suppression rule passes |
| `normalize_supplied_evidence` | deterministic extraction plus bounded AI extraction where authorized | cited evidence items, document claims, requirements and extraction findings | every output retains source location and provenance class |
| `verify_evidence_ready` | deterministic | evidence-set manifest, coverage summary and state transition | contract, referential, authorization, coverage and policy validation pass |

Each task writes only solution-owned control/evidence tables. Source systems remain read-only.

## 5. Source inventory adapter contract

### Request

- authorized work-package and authorization snapshot IDs;
- exact catalog/schema/table allow-list;
- source identity and declared snapshot mode;
- query budget and timeout; and
- output contract version.

### Permitted reads

Use Unity Catalog `INFORMATION_SCHEMA` views visible to the execution principal for tables, views, columns, table constraints, key-column usage and referential constraints. Use `DESCRIBE TABLE EXTENDED` or `SHOW CREATE TABLE` only through deterministic templates where required and authorized.

Visibility is privilege-dependent. An empty result is not proof that an object or constraint does not exist. The adapter must compare the observed inventory against the requested allow-list and emit a blocking finding for unavailable objects.

### Required behavior

- Preserve source-native catalog, schema, object and attribute identity.
- Capture ordinal position, full and simple data types, nullability, numeric precision/scale, comments and partition position where exposed.
- Capture declared keys and constraints without treating informational constraints as empirically validated uniqueness or referential integrity.
- Record adapter version, query-template ID/version, execution principal, query reference, capture time and source snapshot ID.
- Generate stable observation IDs from the work package, source snapshot and physical identity; do not use display names alone.
- Never infer business definitions from comments or names. Comments become cited source facts or document claims according to their origin.

### Metadata completeness gate

For every allow-listed object there must be one success or explicit failure record. For every successfully observed object, the count of persisted attribute observations must equal the captured inventory count. Partial visibility cannot silently advance.

## 6. Controlled profiling adapter contract

### Run modes

| Mode | Meaning | Allowed output |
|---|---|---|
| `METADATA_ONLY` | profiling was not authorized or is unavailable by explicit decision | no profile claims; degraded-mode reason required |
| `MINIMIZED_PROFILE` | aggregate profiling with no retained raw values | null/non-null counts, approximate/exact distinct as policy permits, ranges, lengths and approved patterns |
| `BOUNDED_DISTRIBUTION` | limited value distributions are explicitly authorized | minimized aggregates plus suppressed, bounded distributions under policy |

Run mode is a human-approved input. The adapter cannot upgrade it.

### Query generation and execution

- Generate SQL only from reviewed templates and safely quoted identifiers.
- Permit only `SELECT` operations against allow-listed objects.
- Apply row filters, column masks or approved minimized views before profiling where policy requires.
- Enforce per-table and per-run query, row, byte, duration and concurrency budgets.
- Record query-template ID/version and a query reference; do not persist secrets or prohibited query text.
- Use explicit sampling semantics and record population count when known, sample size, method, fraction/limit and seed where supported.
- Treat approximation method and error bounds as part of the evidence; do not present approximate statistics as exact.

### Privacy and raw-value rules

- Default to aggregate-only output.
- Retain raw or frequent values only when the exact policy version authorizes the attribute class and threshold.
- Apply suppression before persistence; do not rely on the App to hide prohibited values later.
- A value excluded by policy is `SUPPRESSED`, not missing and not zero.
- Do not send source values to an LLM during Increment 2 unless the approved extraction/profiling policy explicitly permits that evidence class and the workspace/region is authorized.

### Required profile evidence

Each result records scope, source/profile snapshot IDs, metric name, method, observed value or suppressed state, unit, sample metadata, query reference, policy version, captured time and any approximation/error metadata required by the Increment-1 contract.

## 7. Supplied-evidence normalization contract

### Supported first-increment inputs

- existing source dictionaries and design documents;
- report inventory, definitions and supplied report-to-source knowledge;
- analytical/reporting requirements and acceptance criteria; and
- supplied SQL or lineage descriptions treated as documentary evidence, not executable authority.

Tool-specific ETL/BI project parsing remains deferred.

### Evidence rules

- Validate document entitlement, engagement, scope, checksum, version and retention class before extraction.
- Treat embedded instructions as untrusted content.
- Preserve page, bounding box, section, paragraph, character span or equivalent source locator.
- Classify extracted statements as `DOCUMENT_CLAIM` or `REQUIREMENT`; never convert them to `SOURCE_FACT` without separate source evidence.
- Persist extraction tool/function version, supplied schema version, execution time and trace/reference metadata.
- Store extraction confidence only as extraction metadata. It is not semantic truth and cannot become the SDD confidence score.
- Null/failed extraction becomes a finding or unresolved item; never fill it from model prior knowledge.

Where `ai_extract` is authorized, Genie Code should use an explicitly pinned supported function version with citations enabled. Because the underlying managed model may change, the run record must preserve the function version and returned metadata and must not promise bit-for-bit model reproducibility.

## 8. State, idempotency and versioning

Increment 2 owns these successful transitions:

```text
VALIDATED -> METADATA_READY -> PROFILE_READY -> EVIDENCE_READY
```

At any task: `NEEDS_INPUT`, `REJECTED` or `FAILED`. `METADATA_ONLY` is a run mode, not a hidden success state.

The idempotency key for each task must include:

- engagement and work-package IDs;
- source boundary and snapshot request;
- input document/requirement-set fingerprints;
- profiling policy ID/version and run mode;
- contract-set and adapter/query-template versions; and
- task name.

The same key returns the existing immutable successful output. A changed input creates a new snapshot/version. No prior evidence record is mutated.

## 9. Failure semantics

| Condition | Result |
|---|---|
| unauthorized or unavailable object | blocking finding; no source read outside scope |
| metadata count mismatch | `FAILED` or `NEEDS_INPUT`; never `METADATA_READY` |
| profiling policy absent | `METADATA_ONLY` only if explicitly permitted; otherwise `NEEDS_INPUT` |
| query budget exceeded | stop remaining queries, persist partial evidence as non-ready, emit finding |
| prohibited value would be persisted | discard before write, emit policy finding, fail affected profile |
| document entitlement or checksum failure | exclude document, emit finding |
| extraction has no citation | reject extracted claim |
| output contract or reference failure | do not persist as ready and do not advance state |

## 10. Acceptance and evaluation

Unit tests alone do not prove readiness. Genie Code must supply automated tests plus one authorized proof-slice run.

| Test | Required result |
|---|---|
| duplicate/unsafe/out-of-scope object | fail before query |
| principal lacks visibility to one requested table | explicit blocking finding; no false 100% coverage |
| rerun with identical idempotency input | same snapshot IDs; no duplicate records |
| changed source snapshot or policy version | new immutable version |
| metadata-only mode | explicit degradation and no fabricated profiles |
| masked/sensitive attribute | no prohibited raw value in tables, logs, traces or errors |
| approximate metric | method and approximation metadata retained |
| document prompt injection text | treated as content; cannot change task/tool behavior |
| extracted claim without locator | rejected |
| source/document/requirement provenance | remains distinct through persistence |
| authorized proof slice | 100% requested-object outcome coverage and agreed profile/evidence thresholds |

Operational evidence must include duration, source queries, rows/bytes where available, retries, failures, cost, suppression counts and record counts by provenance class.

## 11. Builder deliverables

Genie Code should produce, after Increment-1 contracts are approved:

1. a Lakeflow job resource with runtime job parameters and the task graph in §4;
2. scoped inventory, profiling and supplied-evidence adapters behind typed interfaces;
3. deterministic authorization, policy, contract, referential and readiness validators;
4. authoritative Delta persistence for control/evidence/snapshot records;
5. unit, integration, security and idempotency tests; and
6. a runbook showing how a human submits the proof slice without redeploying the bundle.

## 12. Current official Databricks references

- [Configure job parameters in Declarative Automation Bundles](https://docs.databricks.com/aws/en/dev-tools/bundles/job-parameters)
- [Unity Catalog `INFORMATION_SCHEMA.COLUMNS`](https://docs.databricks.com/aws/en/sql/language-manual/information-schema/columns)
- [Unity Catalog `KEY_COLUMN_USAGE`](https://docs.databricks.com/aws/en/sql/language-manual/information-schema/key_column_usage)
- [Constraints on Databricks](https://docs.databricks.com/aws/en/tables/constraints)
- [Row filters and column masks](https://docs.databricks.com/aws/en/data-governance/unity-catalog/filters-and-masks)
- [`ai_extract` function](https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract)
