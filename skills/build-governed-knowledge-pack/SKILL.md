---
name: build-governed-knowledge-pack
description: Create, extend, or version evidence-backed governed insurance knowledge packs for a new LOB, domain, jurisdiction, or approved source update. Use when Codex must research and structure reusable candidate knowledge under this project's canonical manifest/module/glossary/code-set/completeness contracts, preserve claim-level provenance, or validate and prepare a candidate pack for SME, regulatory, licensing, and owner review. Do not use for engagement source evidence, Source Data Dictionary generation, Silver/Gold/STTM artifacts, ontology creation, or pack approval/runtime promotion.
---

# Build Governed Knowledge Pack

Create reusable procedural output; never embed LOB or jurisdiction facts in this skill. Produce only immutable `CANDIDATE` knowledge packs with `runtime_eligible: false`.

## Establish the authoring boundary

1. Read the repository `AGENTS.md`, Requirements Charter, Agent Solution Architecture, knowledge README, canonical structure, schemas, registries, and current pack manifest before changing knowledge.
2. State the pack's LOB, domains, geography/jurisdiction, effective-date boundary, intended users, non-scope, owner, source policy, and target completeness rubric.
3. Classify the request:
   - create a new LOB pack;
   - add or revise a jurisdiction extension;
   - create a new immutable version after governed-source changes; or
   - validate/repair a candidate pack.
4. Stop when the request would modify an immutable version, import engagement/client facts into a public pack, create ontology, reproduce unlicensed content, or grant approval/runtime eligibility.

Read [authoring-contract.md](references/authoring-contract.md) for the canonical layer, version, and output rules. Read [source-and-provenance-policy.md](references/source-and-provenance-policy.md) before researching or writing claims. Read [review-and-evaluation.md](references/review-and-evaluation.md) before scoring or presenting a candidate for review.

## Create an explicit plan

Copy [pack-plan.template.yml](assets/pack-plan.template.yml) outside the skill folder and complete it. Do not infer missing LOB, jurisdiction, owner, source-use authority, or completeness dimensions.

Require:

- a unique lowercase `pack_id` and semantic version;
- an explicit LOB directory and module plan;
- separate insurance-core, LOB, and extension modules;
- completeness dimensions totaling 100%;
- named candidate owner and review roles;
- source records with publisher, URL, class, applicability, usage basis, and verification date; and
- non-scope and prohibitions.

Run the scaffold only after reviewing the plan:

```text
python scripts/scaffold_candidate_pack.py --repository-root <repo> --plan <plan.yml>
```

The scaffold must refuse an existing target version and must not scan directories to infer content.

## Research and author the candidate

1. Prefer official primary sources for jurisdiction rules and current official product/technical documentation for standards.
2. Separate reusable insurance core, LOB semantics, and jurisdiction-specific obligations. Never generalize one jurisdiction to another.
3. Write independent structured interpretations. Store links and concise derived facts; do not copy full publications, forms, manuals, tables, or proprietary wording.
4. Put each material statement in `content.claims` with:
   - stable `claim_id`;
   - concise `statement`;
   - `derivation_type`;
   - `source_ids` or `decision_references`;
   - `source_locator` for exact structured facts;
   - applicability and jurisdiction when relevant;
   - effective-date status and dates when relevant; and
   - assumptions, conflicts, and review roles when needed.
5. Preserve unresolved items. Do not fabricate a source, date, code, form, threshold, definition, or completeness score.
6. Keep ontology, glossary, KPI, code-set, standards, and reference-model content as governed inputs. Ontology creation remains out of scope.

Use LLM judgment for synthesis, semantic separation, contradiction detection, applicability analysis, and gap questions. Use deterministic scripts for identities, paths, schemas, score arithmetic, fingerprints, reference resolution, immutability, and lifecycle gates.

## Validate and finalize

Run the strict finalizer after authoring all declared modules and assets:

```text
python scripts/finalize_and_validate_candidate.py --repository-root <repo> --manifest <manifest-relative-path>
```

The finalizer must:

- refuse non-candidate or runtime-eligible content;
- validate source-registry identities and referenced source IDs;
- require claim-level provenance for new modules;
- recompute the weighted completeness score;
- refresh only explicitly declared manifest fingerprints;
- call the repository pack validator; and
- fail on missing, cross-root, unresolved, duplicated, or structurally invalid references.

Do not weaken validation to make a candidate pass. Record gaps and leave the pack non-runtime-eligible.

## Review and register

1. Run a semantic critic that did not author the claims; treat same-model agreement as correlated evidence.
2. Route LOB/domain semantics to named SMEs, jurisdiction applicability to a regulatory/compliance reviewer, restricted sources to the content-rights owner, and ambiguous high-impact interpretations to legal counsel when needed.
3. Evaluate on an unseen LOB or jurisdiction case; do not reuse answer keys in instructions, templates, scripts, or governed context.
4. Propose the registry entry only after structural validation and recorded reviews. Keep lifecycle `CANONICAL_CANDIDATE`, approval `CANDIDATE`, and runtime eligibility `false`.
5. Never overwrite or silently repair a published version. Create a new version and record lineage/supersession.

## Required output

Return:

- candidate pack path and version;
- declared scope/non-scope;
- source and licensing/usage summary;
- module/asset inventory;
- completeness score with every dimension and gap;
- validation result and fingerprints;
- unresolved contradictions/questions;
- required reviewers and decisions; and
- explicit statement that the candidate is not approved or runtime eligible.

