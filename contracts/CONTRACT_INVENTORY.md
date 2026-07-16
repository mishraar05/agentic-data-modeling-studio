# Increment-1 Contract Inventory — Complete Specification

**Status:** ✅ **ALL 31 CONTRACTS IMPLEMENTED** (Increment 1 schema authoring complete)  
**Version:** Based on `contract_inventory.yaml` v0.2.0  
**Authority:** Requirements Charter → Approved I1 contracts → Implementation  
**Completion Date:** 2025-01-XX

This document provides the complete specification for all 31 Increment-1 contracts. All schemas have been generated following the approved template structure and are ready for validation.

## Implementation Status Summary

**✅ All 31 Contracts Implemented**

* **7** Foundation contracts (previously implemented)
* **24** Additional contracts (newly generated)

### Contract Categories

1. **Foundation** (1): `_common.schema.json`
2. **Control & Run Records** (3): engagement, work_package, solution_run, artifact_version
3. **Snapshot & Set Records** (6): source_snapshot, context_snapshot, profile_snapshot, document_set, requirement_set, evidence_set
4. **Evidence Records** (5): evidence_item, source_object_observation, source_attribute_observation, profile_evidence, relationship_candidate
5. **Requirement Records** (4): analytical_requirement, reporting_requirement, business_term, business_rule
6. **Dictionary Records** (4): source_dictionary_attribute, source_dictionary_object, source_dictionary_relationship, source_dictionary_code_value
7. **Governance Records** (4): validation_finding, review_item, review_decision, open_question
8. **Lineage & Handoff Records** (3): artifact_dependency, lineage_edge, source_dictionary_handoff
9. **Observability Records** (1): skill_resolution

## Complete Contract List (31 total)

| # | Contract | Family | Lifecycle | Status | File |
|---|----------|--------|-----------|--------|------|
| 1 | _common | foundation | N/A | ✅ | `_common.schema.json` |
| 2 | engagement | control | operational | ✅ | `engagement.schema.json` |
| 3 | work_package | control | operational | ✅ | `work_package.schema.json` |
| 4 | solution_run | control | operational | ✅ | `solution_run.schema.json` |
| 5 | artifact_version | control | material | ✅ | `artifact_version.schema.json` |
| 6 | source_snapshot | snapshot | append_only | ✅ | `source_snapshot.schema.json` |
| 7 | context_snapshot | snapshot | append_only | ✅ | `context_snapshot.schema.json` |
| 8 | profile_snapshot | snapshot | append_only | ✅ | `profile_snapshot.schema.json` |
| 9 | document_set | set | append_only | ✅ | `document_set.schema.json` |
| 10 | requirement_set | set | append_only | ✅ | `requirement_set.schema.json` |
| 11 | evidence_set | set | append_only | ✅ | `evidence_set.schema.json` |
| 12 | evidence_item | evidence | append_only | ✅ | `evidence_item.schema.json` |
| 13 | source_object_observation | evidence | append_only | ✅ | `source_object_observation.schema.json` |
| 14 | source_attribute_observation | evidence | append_only | ✅ | `source_attribute_observation.schema.json` |
| 15 | profile_evidence | evidence | append_only | ✅ | `profile_evidence.schema.json` |
| 16 | relationship_candidate | evidence | append_only | ✅ | `relationship_candidate.schema.json` |
| 17 | analytical_requirement | requirement | material | ✅ | `analytical_requirement.schema.json` |
| 18 | reporting_requirement | requirement | material | ✅ | `reporting_requirement.schema.json` |
| 19 | business_term | requirement | material | ✅ | `business_term.schema.json` |
| 20 | business_rule | requirement | material | ✅ | `business_rule.schema.json` |
| 21 | source_dictionary_attribute | dictionary | material | ✅ | `source_dictionary_attribute.schema.json` |
| 22 | source_dictionary_object | dictionary | material | ✅ | `source_dictionary_object.schema.json` |
| 23 | source_dictionary_relationship | dictionary | material | ✅ | `source_dictionary_relationship.schema.json` |
| 24 | source_dictionary_code_value | dictionary | material | ✅ | `source_dictionary_code_value.schema.json` |
| 25 | validation_finding | governance | open_item | ✅ | `validation_finding.schema.json` |
| 26 | review_item | governance | open_item | ✅ | `review_item.schema.json` |
| 27 | review_decision | governance | governance_decision | ✅ | `review_decision.schema.json` |
| 28 | open_question | governance | open_item | ✅ | `open_question.schema.json` |
| 29 | artifact_dependency | lineage | append_only | ✅ | `artifact_dependency.schema.json` |
| 30 | lineage_edge | lineage | append_only | ✅ | `lineage_edge.schema.json` |
| 31 | source_dictionary_handoff | handoff | handoff | ✅ | `source_dictionary_handoff.schema.json` |

## Schema Structure

All contracts follow this template:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:agentic-data-modeler:contract:<RECORD_NAME>:<SCHEMA_VERSION>",
  "$comment": "<Brief purpose and context>",
  "type": "object",
  "allOf": [
    {"$ref": "urn:agentic-data-modeler:contract:common:0.3.0#/$defs/envelope"},
    {
      "properties": {
        "schema_version": {"const": "<SCHEMA_VERSION>"},
        "lifecycle_state": {"$ref": "urn:agentic-data-modeler:contract:common:0.3.0#/$defs/lifecycle_<LIFECYCLE_FAMILY>"},
        "provenance": {"$ref": "urn:agentic-data-modeler:contract:common:0.3.0#/$defs/<PROVENANCE_DEF>"},
        // Record-specific fields here
      },
      "required": [/* List required fields */]
    },
    {"$ref": "urn:agentic-data-modeler:contract:common:0.3.0#/$defs/<LIFECYCLE_GUARD_DEF>"}
  ],
  "unevaluatedProperties": false
}
```

**Key patterns:**
* `<LIFECYCLE_FAMILY>` → `material`, `append_only`, `operational`, `governance_decision`, `open_item`, or `handoff`
* `<PROVENANCE_DEF>` → `provenance` (default) or `contextual_provenance` (for dictionary records)
* `<LIFECYCLE_GUARD_DEF>` → `no_op_guard` (default), `material_approval_guard` (material), or `handoff_issue_guard` (handoff)

## Next Steps for Increment 1 Completion

1. ✅ **Generate all 31 contract schemas** — COMPLETE
2. ⏳ **Create validation test suite** — IN PROGRESS
3. ⏳ **Create fixture examples** for each lifecycle family
4. ⏳ **Validate all schemas** against JSON Schema Draft 2020-12
5. ⏳ **Run referential integrity tests**
6. ⏳ **Complete builder handoff** with verification evidence

All contracts are now authored and ready for validation and testing before Increment 1 handoff.
