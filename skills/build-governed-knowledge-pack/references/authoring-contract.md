# Knowledge-pack authoring contract

## Purpose

Use this contract to create a reusable governed input, not a Source Dictionary, model, mapping, ontology, or client evidence store.

## Layer separation

| Layer | Content | Prohibition |
|---|---|---|
| `insurance_core` | Cross-LOB insurance concepts supported across the declared scope | Do not place one LOB's product rules here |
| `lob` | LOB-specific risks, coverages, lifecycles, KPIs and analytical semantics | Do not generalize jurisdiction rules |
| `extension` | Jurisdiction, enterprise, product or platform-specific overrides/additions | Do not silently override higher-precedence approved evidence |

Keep each claim in the narrowest applicable layer. Record dependencies explicitly.

## Candidate lifecycle

1. Create a new semantic version; never modify an immutable published version.
2. Set pack, source registry and modules to `CANDIDATE` and `runtime_eligible: false`.
3. Treat the manifest as the sole content authority. List every module and governed asset explicitly.
4. Compute SHA-256 only after authoring. Any later content edit intentionally invalidates the manifest until refinalized.
5. Register a candidate only after structural validation. Approval and runtime promotion are separate human-governed actions.

## Required pack components

- `manifest.yml` and `completeness.yml`;
- governed source registry;
- explicit insurance-core, LOB and extension modules;
- glossary, code sets, KPI/standards/reference assets when applicable;
- scope, non-scope, owners, review requirements, dependencies and prohibitions;
- claim-level provenance for every material fact, definition, obligation, threshold and modeling rule; and
- unresolved gaps rather than invented content.

## Claim contract

Use `content.claims` for new generic modules:

```yaml
claims:
  - claim_id: stable_lowercase_id
    statement: Concise independently worded structured knowledge.
    derivation_type: independent_paraphrase
    source_ids: [registered_source_id]
    source_locator: section_or_page_when_available
    applicability: declared_scope
    jurisdiction: US_XX
    effective_date_status: KNOWN
    effective_from: "YYYY-MM-DD"
    assumptions: []
    conflicts: []
    review_roles: [lob_sme, jurisdiction_reviewer]
```

Allowed derivation types are `exact_structured_fact`, `independent_paraphrase`, `modeling_inference`, and `sme_decision`. An SME decision uses `decision_references`; the others cite registered `source_ids`. Exact facts require a locator. Jurisdiction claims require jurisdiction and effective-date status. Use `UNRESOLVED` rather than guessing a date.

## Precedence

Apply this order unless an approved enterprise policy states otherwise:

1. approved client evidence and engagement decisions;
2. approved enterprise, jurisdiction, product and platform extensions;
3. approved public core/LOB knowledge;
4. unresolved candidate background.

Candidate public knowledge never overrides policy wording, authoritative source evidence, or approved human decisions.

