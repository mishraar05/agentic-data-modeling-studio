# ADR-001: Canonical versioned knowledge-pack structure

**Status:** Accepted  
**Date:** 2026-07-15  
**Decision owner:** Solution owner  

## Context

Knowledge was initially stored by asset type and later represented through a second business-oriented folder tree. That created two possible authorities, inconsistent pack identities, and no enforceable runtime-selection contract.

## Decision

The canonical authority is `knowledge/packs/<pack_id>/<version>/manifest.yml`. Business knowledge is organized into Insurance Core, Personal Auto, and Extensions modules. Each module owns its glossary, entities, relationships, lifecycle, code-set metadata, analytics, sources, and assessment as applicable.

Repository-wide `schemas/`, `registry/`, and `sources/` provide contracts and discovery, not a second content authority. Ontology and target reference models are governed references inside a pack. Modeling standards are versioned pack assets.

Pack and module selection must be manifest-driven, approval-aware, version-exact, scope-filtered, and fail closed. Candidate content may be synchronized for development but cannot enter runtime context unless both registry and manifest authorize it.

The existing `v0.1.0` and `v0.2.0` manifests remain immutable at their current paths. They are registered as legacy development history; moving them would invalidate existing paths and fingerprints. `v0.3.0` is the first canonical modular pack.

## Consequences

- There is one content authority per pack version.
- Completeness is assessed at pack and module levels without implying correctness or approval.
- Enterprise, product, jurisdiction, and platform variability cannot leak into the reusable core.
- New knowledge must validate against schemas before registration.
- Further public-content expansion pauses until structural and runtime guardrails pass.

