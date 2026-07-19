# Contract builder handoff

**Current contract set:** `0.3.0`

**Shared vocabulary:** `common:0.4.0`

**Record contracts:** 29

The contract set is run-rooted. `solution_run` is the single execution and source
authorization boundary. `source_snapshot` and `evidence_set` freeze source facts;
`context_snapshot` freezes the bounded semantic context used by an agent call.

## Builder requirements

- Generate one Delta table for every `*.schema.json` except `_common.schema.json`.
- Treat Delta records as authoritative and spreadsheets/apps as projections.
- Validate JSON Schema Draft 2020-12, closed properties, lifecycle guards, and
  referenced common-schema versions before producing DDL.
- Require same-run source facts and exact context snapshots for semantic outputs.
- Validate that every observed or inferred claim cites an allowed evidence item.
- Never approve LLM-authored material output without a recorded human decision.

## Relationship-agent boundary

`relationship_candidate` is a material, reviewable output. The producer model gets
only the frozen source inventory, approved governed knowledge, approved prior
decisions from the same memory partition, and explicit evidence locators. A
different model endpoint critiques the proposal. Deterministic code rejects
invented objects, attributes, evidence references, unsupported relationship types,
or over-budget context before records are written.

## Verification

The handoff is accepted when:

1. all 29 contract files and the common schema parse and validate;
2. generated DDL has the same 29-table inventory;
3. source-to-context-to-relationship workflow wiring validates;
4. relationship tests prove grounded output, invented-citation rejection, critic
   execution, and reuse of an approved prior decision; and
5. repository scans find no obsolete identity keys or fixed proof-slice IDs.
