# ADR-007 — Schema-scoped source discovery with a frozen manifest

**Status:** Accepted  
**Decision date:** 2026-07-18  
**Owner decision:** Generate the Source Data Dictionary for all eligible tables without requiring a manually maintained table list.

## Context

The Source Data Dictionary must cover 100% of every in-scope source object and attribute. The initial proof slice represented scope as seven explicitly supplied tables. That is safe for a bounded test but does not scale to a poorly documented source estate containing tens or hundreds of tables.

Removing the boundary entirely would allow an erroneous configuration to read unrelated schemas or newly added sensitive objects without a reproducible record of what was processed.

## Decision

The authorization boundary is the selected catalog and schema plus a governed source-scope policy. The normal production mode is `SCHEMA_ALL_TABLES`. The runtime deterministically discovers every metadata-visible eligible table, applies approved object-type and exclusion rules, sorts the result, and freezes it as the execution manifest before metadata capture or profiling.

Three scope modes are supported:

- `SCHEMA_ALL_TABLES` — every eligible table in one authorized schema;
- `PATTERN_BASED` — objects matching governed include patterns after governed exclusions; and
- `EXPLICIT_TABLES` — a small, explicitly selected set for proof slices or targeted reruns.

The resolved manifest is stored in the existing work-package table boundary and included in the source-snapshot fingerprint. Every downstream task must use that frozen manifest. A later discovery that resolves differently is source drift and cannot silently mutate an existing work package.

## Consequences

### Gains

- no table-by-table maintenance for the normal full-schema dictionary run;
- measurable 100% coverage against the frozen manifest;
- reproducible evidence of exactly which tables were processed;
- deterministic detection of added, removed, hidden, or excluded tables; and
- continued engagement, catalog, schema, identity, cost, and privacy isolation.

### Costs and limitations

- discovery becomes a mandatory job task;
- exclusions and eligible object types are governed configuration;
- a changed schema requires a new work-package version or explicit drift handling;
- the current task-value transport is bounded and must later move to a durable manifest table for very large schemas; and
- identifiers outside the current contract pattern fail closed rather than being silently skipped.

## Anti-drift evidence

- **Charter deliverable:** reconstructed Source Data Dictionary.
- **Scope:** reusable cross-cutting source onboarding for any selected LOB/domain; first exercised by E-123 / WP-1234, P&C Personal Auto / Policy.
- **Acceptance:** every eligible discovered table appears once in the frozen manifest; metadata/profile coverage reconciles to 100%; exclusions and drift are visible and reproducible.
- **Why now:** full-estate dictionary generation is a current product requirement, whereas manually enumerating proof-slice tables prevents the next scaling step.
