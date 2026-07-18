# Increment 2–3 Contract Dependency Matrix

**Status:** Implementation working record; architecture/contract-owner acceptance pending

**Scope:** US P&C Personal Auto — California, Guidewire PolicyCenter proof slice

**Governing deliverable:** Reconstructed Source Data Dictionary

**Contract set reviewed:** `contract_inventory.yaml` `0.2.0`, common vocabulary
`0.3.0`, and the 31 record schemas currently published under `contracts/`

## Anti-drift gate

This work advances the Reconstructed Source Data Dictionary by establishing the
contract-owned records needed to collect source facts and assemble governed
context. It serves the selected California Personal Auto proof slice while
keeping the implementation reusable across LOBs and domains. Acceptance
requires an owner-reviewed dependency matrix, fail-closed runtime validation,
and later an authorized proof-slice run with complete source-object outcomes.
It belongs now because the contract tables exist and source onboarding is the
next prerequisite; semantic dictionary inference, Silver, Gold, STTM, and
tool-specific conversion remain downstream.

## Record ownership

| Work package | Authoritative output | Contract and version | Ownership decision |
|---|---|---|---|
| `I23-01` runtime request | Engagement authorization boundary | `engagement` `0.1.0` | `engagement.authorization_ref`, source access, profiling policy, and output boundary are authoritative. |
| `I23-01` runtime request | Bounded source scope and workflow state | `work_package` `0.1.0` | Owns engagement reference, LOB/domain through the common envelope, source allow-list, target boundary, and workflow state. |
| `I23-01` execution | Bounded run record | `solution_run` `0.1.0` | Owns work-package reference, run type, timestamps, status, error, and cost. |
| `I23-02` metadata | Metadata snapshot manifest | `source_snapshot` `0.1.0` | Owns captured counts, query reference, time, and fingerprint. |
| `I23-02` metadata | Object observations | `source_object_observation` `0.1.0` | Owns one observed source object and captured constraint observations. |
| `I23-02` metadata | Attribute observations | `source_attribute_observation` `0.1.0` | Owns physical attribute facts and constraint role. |
| `I23-03` profiling | Profile snapshot manifest | `profile_snapshot` `0.1.0` | Owns profiling mode, counts, query reference, time, and fingerprint. |
| `I23-03` profiling | Attribute profile facts | `profile_evidence` `0.1.0` | Owns counts, bounded scalar values, and approved top-value/pattern evidence. |
| `I23-02`/`I23-03` | Evidence identity and provenance | `evidence_item` `0.1.0` | Owns provenance class, evidence type/content, source references, and fingerprint. |
| `I23-03` | Candidate physical relationships | `relationship_candidate` `0.1.0` | Owns evidence-linked parent/child candidates; does not establish semantic truth. |
| `I23-04` supplied evidence | Document inventory | `document_set` `0.1.0` | Owns authorized locators, count, ingestion time, and fingerprint. |
| `I23-04` supplied evidence | Supplied requirements manifest | `requirement_set` `0.1.0` | Owns requirement counts, optional document reference, time, and fingerprint. |
| `I23-04` supplied evidence | Extracted requirements and claims | `analytical_requirement`, `reporting_requirement`, `business_term`, `business_rule` `0.1.0` | Preserve requirement/document provenance; no source-fact promotion. |
| `I23-05` readiness | Immutable evidence manifest | `evidence_set` `0.1.0` | Owns source/profile/document/requirement references, item count, time, and fingerprint. |
| `I23-01`–`I23-08` validation | Findings and unresolved questions | `validation_finding`, `open_question` `0.1.0` | Own deterministic failures and human-input gaps; never hide them in logs only. |
| `I23-06`–`I23-08` context | Immutable context manifest | `context_snapshot` `0.1.0` | Owns exact knowledge selection, selected modules, budgets, effective date, and fingerprint. |
| `I23-08` dependency tracking | Artifact dependency edges | `artifact_dependency`, `lineage_edge` `0.1.0` | Own immutable dependencies and lineage references used for invalidation. |

Every record above also consumes the common envelope and provenance definitions
from `_common` `0.3.0`. `_common` is a schema foundation, not a durable table.

## Blocking contract or decision gaps

| ID | Gap | Impact | Required disposition |
|---|---|---|---|
| `CG-I23-01` | The onboarding specification names `MINIMIZED_PROFILE` and `BOUNDED_DISTRIBUTION`, but `profile_snapshot` `0.1.0` permits only `FULL`, `METADATA_ONLY`, and `RESTRICTED`. | Profiling-mode persistence cannot conform to both authorities. | Contract/architecture owner must select and version one vocabulary. Until then, runtime validation follows the approved contract and profiling execution does not advance. |
| `CG-I23-02` | No dedicated authorization-snapshot contract exists. `engagement.authorization_ref` is the only approved authorization link. | An immutable authorization snapshot cannot be persisted under a new record type. | Use the approved engagement reference without inventing a table, or approve a versioned contract change. |
| `CG-I23-03` | The runtime specification requires exact profiling policy ID/version and contract-set version, but `work_package` stores neither. The approved contract-set identity is inventory version `0.2.0`. | These values can be validated at runtime but cannot be added to the work-package record. | Contract owner must identify an approved persistence owner or version the contract before persistence. |
| `CG-I23-04` | `validation_finding` requires `artifact_version_ref`, but pre-artifact request/authorization failures occur before an artifact version necessarily exists. | Early fail-closed findings lack a conforming durable owner. | Contract owner must specify the bootstrap artifact-version policy or version the finding contract. |

## Current implementation boundary

The current safe build slice may:

1. expose per-run Lakeflow job parameters;
2. parse and validate a typed source-discovery request;
3. reject missing, placeholder, malformed, duplicate, unsafe, or cross-boundary scope;
4. produce a deterministic request fingerprint for idempotency; and
5. prove those controls with unit and security tests.

It must not query source objects, execute profiling, persist a new record shape,
or advance a work package beyond `VALIDATED` until the applicable human
decisions and contract gaps above are resolved.
