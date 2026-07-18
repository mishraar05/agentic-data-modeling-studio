# Canonical knowledge structure

```text
knowledge/
|-- archive/
|   `-- pre_canonical_v0.1.0_v0.2.0/
|-- packs/
|   `-- public_us_pnc_personal_auto/
|       |-- 0.3.0/                       # preserved superseded candidate
|       |-- 0.4.0/                       # preserved superseded candidate
|       |-- 0.5.0/                       # preserved superseded candidate
|       `-- 0.6.0/                       # current canonical approved runtime pack
|           |-- manifest.yml
|           |-- completeness.yml
|           |-- glossary/
|           |   `-- business_terms.yml
|           |-- code_sets/
|           |   `-- personal_auto_semantic_codes.yml
|           |-- standards/
|           |-- references/
|           |   |-- ontology/
|           |   `-- target_reference_models/
|           |-- insurance_core/
|           |   |-- party/
|           |   |-- policy/
|           |   |-- product_and_coverage/
|           |   |-- claims/
|           |   |-- billing/
|           |   `-- common_analytics/
|           |-- personal_auto/
|           |   |-- risk_and_vehicle/
|           |   |-- driver_and_household/
|           |   |-- coverages/
|           |   |-- policy_lifecycle/
|           |   |-- claims_lifecycle/
|           |   `-- kpis/
|           `-- extensions/
|               |-- jurisdiction/
|               |-- enterprise/
|               |-- product/
|               `-- platform/
|-- registry/
|-- schemas/
|-- sources/
|-- README.md
`-- CANONICAL_STRUCTURE.md
```

`packs/<pack_id>/<version>/manifest.yml` is the sole content authority. Archive, registry, schemas, and sources support governance; they are not competing knowledge stores. Published candidate versions are preserved and superseded through the registry, never edited in place.

For a new LOB, use the same versioned pattern with a LOB-specific directory rather than copying `personal_auto` as a semantic assumption:

```text
packs/<pack_id>/<version>/
|-- manifest.yml
|-- completeness.yml
|-- glossary/
|-- code_sets/
|-- standards/
|-- references/
|-- insurance_core/
|-- <lob>/
`-- extensions/
    |-- jurisdiction/
    |-- enterprise/
    |-- product/
    `-- platform/
```

New generic LOB modules use `layer: lob`; `layer: personal_auto` remains accepted only for compatibility with immutable existing Personal Auto versions. The [`build-governed-knowledge-pack`](../skills/build-governed-knowledge-pack/SKILL.md) maintainer skill creates candidate structure from an explicit plan and never infers content by scanning directories.
