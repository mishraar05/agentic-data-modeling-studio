# Governed knowledge layer

This directory contains versioned, authorized inputs for the Agentic Data Analyst and Modeler. Ontology is a governed input and is never a solution deliverable.

See [`CANONICAL_STRUCTURE.md`](CANONICAL_STRUCTURE.md) for the physical tree.

## Canonical authority

The sole content authority is:

`knowledge/packs/<pack_id>/<version>/manifest.yml`

Agents and tools must not scan directories for knowledge. They select an exact pack version through `knowledge/registry/pack_registry.yml`, validate its manifest and fingerprints, enforce approval and runtime eligibility, then select only scope-applicable modules.

## Structure

| Path | Purpose |
|---|---|
| `archive/` | Immutable pre-canonical `v0.1.0` and `v0.2.0` development history |
| `packs/` | Canonical immutable versioned knowledge content |
| `registry/` | Exact pack/version discovery and source-registry policy |
| `schemas/` | Contracts for manifests, modules, glossary, code sets, KPIs, and completeness |
| `sources/` | Governed source provenance and usage basis |

## Canonical pack layout

Each versioned pack contains its manifest and completeness assessment, pack-level modeling/STTM standards, governed ontology and target-reference inputs, reusable Insurance Core modules, LOB-specific modules, and isolated jurisdiction, enterprise, product, and platform extensions.

Each module owns its scope, content, sources, dependencies, review requirements, approval state, and runtime eligibility.

## Candidate authoring automation

Use [`build-governed-knowledge-pack`](../skills/build-governed-knowledge-pack/SKILL.md) to scaffold, research, structure, provenance-audit, fingerprint, and validate a new LOB/jurisdiction candidate or immutable candidate version. The skill operates outside the runtime modeling harness and cannot approve a pack or set runtime eligibility.

## Non-negotiable rules

- Candidate, rejected, expired, unauthorized, missing, ambiguous, or cross-version knowledge fails closed.
- Registry and manifest must both authorize the exact version for runtime use.
- Client evidence and approved engagement decisions take precedence over reusable background knowledge.
- No client data, PII, credentials, connection strings, or unlicensed proprietary content belongs in repository packs.
- Generated dictionaries, models, mappings, or inferred concepts belong in solution artifact stores—not in this layer.
- Completeness measures scoped coverage only; it does not prove correctness, licensing, or production readiness.
