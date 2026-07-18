# SDD Agent — Pseudocode (for understanding, not production)

This is a plain-language walkthrough of the Source Data Dictionary agent as code.
It is **not** runnable — it exists so the flow is easy to follow and explain.

### How to read the tags on each step

| Tag | Meaning |
|---|---|
| `[CODE]`   | Deterministic code — facts, math, rules. No LLM. |
| `[LLM]`    | A language-model call — judgment. Must cite evidence. |
| `[HUMAN]`  | A person acts — approve / reject / answer. |
| `[GATE]`   | Fail-closed checkpoint — stop unless conditions are met. |
| `[MEM r]` / `[MEM w]` | Reads memory / writes a durable record. |
| `[STATUS]` | What exists in the repo **today** (built / stub / not built). |

Trust vocabulary every claim carries: **OBSERVED** (a fact) · **INFERRED** (LLM
conclusion, must cite evidence) · **DECIDED** (a human decided) · **UNRESOLVED**
(not enough evidence — becomes an open question, never a guess).

---

## Top level — the whole agent

```python
def run_sdd_agent(scope):
    # scope = { engagement, lob, domain, allow_listed_source_tables }

    ctx      = phase0_assemble_context(scope)          # [GATE][MEM r]
    evidence = phase1_ingest_evidence(ctx)             # [CODE]
    rels     = phase2_detect_relationships(evidence)   # [CODE]

    # --- the repair loop: try, validate, fix, retry (bounded) ---
    for attempt in range(MAX_REPAIRS):
        objects    = phase3_analyze_objects(ctx, evidence, rels)      # [LLM]
        attributes = phase4_analyze_attributes(ctx, evidence, rels)   # [LLM]
        findings   = phase5_find_contradictions(objects, attributes, ctx)  # [CODE + LLM critic]

        draft  = assemble_draft(objects, attributes, rels, findings)
        draft  = phase6_score_confidence(draft)        # [CODE]
        result = phase7_validate_contracts(draft)      # [GATE][CODE]

        if result.ok:
            break                                      # good draft, leave the loop
        # else: loop again, using result.errors as repair guidance
    else:
        raise CannotProduceValidDraft(result.errors)   # gave up after MAX_REPAIRS

    review = phase8_human_review(draft)                # [HUMAN][GATE][MEM w]
    phase9_persist_and_publish(review)                 # [CODE][MEM w]
    return review
```

The single most important idea: **code establishes facts, the LLM proposes meaning
(and must cite evidence), a human approves.** Nothing becomes `APPROVED` on its own.

---

## Phase 0 — Assemble the context (this is where memory is read)

```python
def phase0_assemble_context(scope):                    # [GATE][MEM r]
    assert_valid_scope(scope)                          # no placeholders, allow-listed tables only  [CODE][GATE]

    pack  = select_approved_pack(scope)                # SEMANTIC memory (knowledge pack)  [MEM r]
                                                       #   fails closed if no APPROVED + runtime-eligible pack
    prior = load_prior_decisions(scope)                # EPISODIC memory  [MEM r]
                                                       #   past review_decisions + open_questions for THIS engagement/scope

    envelope = build_context_envelope(
        scope         = scope,
        knowledge     = pack.slice_for(scope),         # only the relevant glossary/code-sets/standards
        prior_context = prior,                         # "already decided X about this table" ; open questions to close
    )
    save_context_snapshot(envelope)                    # provenance, for reproducibility
    return envelope

    # [STATUS] select_approved_pack .......... BUILT  (knowledge/registry.py)
    #          load_prior_decisions ........... NOT BUILT
    #          build_context_envelope ......... NOT BUILT
    #          save_context_snapshot .......... NOT BUILT  (code today hard-codes context_snapshot_id = None)
    #          --> This is the missing memory read-path. See ADR-006.
```

---

## Phase 1 — Ingest evidence (raw facts only, no LLM)

```python
def phase1_ingest_evidence(ctx):                       # [CODE]
    facts = []
    for table in ctx.allow_listed_tables:
        meta = read_metadata(table)                    # columns, keys, types, constraints (read-only tool)
        prof = read_profile(table)                     # null/distinct stats, value distributions (if available)
        facts.append(record_observation(meta, prof))   # [MEM w] source_object/attribute_observation, profile_evidence
    return facts

    # Everything here is OBSERVED — pure fact. The model has not run yet.
    # [STATUS] metadata read .... PARTIAL (evidence/metadata.py)
    #          profiling ......... NOT BUILT  --> degrades to metadata-only, which weakens later inference
```

## Phase 2 — Detect relationship candidates (still just code)

```python
def phase2_detect_relationships(evidence):             # [CODE]
    candidates  = declared_keys(evidence)              # authoritative (real constraints)
    candidates += heuristic_matches(evidence)          # name / type / value-overlap guesses, each with a support score

    surfaced = [c for c in candidates if c.declared or c.score >= THRESHOLD]
    # weak candidates are kept for audit but hidden from the LLM (never silently dropped)
    return surfaced
```

## Phase 3 — Analyze each object's meaning (LLM)

```python
def phase3_analyze_objects(ctx, evidence, rels):       # [LLM]
    results = []
    for obj in evidence.objects:
        bundle   = gather(obj, evidence, rels, ctx.knowledge, ctx.prior_context)
        proposal = LLM.analyze(bundle, skill="SA1")    # PROCEDURAL memory (a skill = a how-to playbook)
        #   proposal = business name, purpose, subject area, synonyms

        for field in proposal:
            field.trust = classify_trust(field)        # OBSERVED / INFERRED / DECIDED / UNRESOLVED
            if field.trust == INFERRED and not field.cites_evidence:
                field.trust = UNRESOLVED
                write_open_question(obj, field)         # [MEM w] never guess — ask instead
        results.append(proposal)
    return results

    # HARD RULE: insufficient evidence -> UNRESOLVED + open_question. Enforced again in Phase 7.
    # [STATUS] NOT BUILT — an approved pack now exists; governed context and the semantic harness remain to be built.
```

## Phase 4 — Analyze each attribute (LLM)

```python
def phase4_analyze_attributes(ctx, evidence, rels):    # [LLM]
    for attr in evidence.attributes:
        propose_meaning(attr, skill="SA1")             # name, definition, lifecycle meaning
        if attr.is_coded:
            map_code_values(attr, skill="SA2")         # values -> governed code set; unmapped ones flagged, never invented
        if looks_sensitive(attr):
            candidate = classify_privacy(attr, skill="SA3")   # CANDIDATE only
            route_to(privacy_steward, candidate)       # agent NEVER finalizes a privacy class
    # [STATUS] NOT BUILT (SA1/SA2/SA3 skills unwritten; depends on approved pack).
```

## Phase 5 — Find contradictions and gaps (code + an independent critic)

```python
def phase5_find_contradictions(objects, attributes, ctx):   # [CODE + LLM critic]
    findings  = deterministic_checks(objects, attributes, ctx)  # term conflicts, superseded decisions, coverage gaps  [CODE]

    critic    = LLM_2.critique(objects, attributes, rubric)     # ideally a DIFFERENT model + reduced context  [LLM]
    findings += critic.findings
    # WARNING: if the critic shares the producer's model/context, its agreement is
    #          correlated, not independent. Independence is the top open risk (ADR-005 F1).
    return findings
    # [STATUS] NOT BUILT.
```

## Phase 6 — Score confidence (code)

```python
def phase6_score_confidence(draft):                    # [CODE]
    for item in draft.items:
        item.confidence = {
            "evidence_type":   rank(item.evidence),     # declared key > profile stat > glossary match > lone inference
            "evidence_count":  count(item.evidence),
            "critic_agreement": item.critic_status,
        }
    return draft
    # Confidence is reported as its PARTS, not one opaque number.
    # It is a triage signal only — meaningless as an accuracy figure until calibrated on unseen data.
```

## Phase 7 — Validate against contracts (fail-closed gate)

```python
def phase7_validate_contracts(draft):                  # [GATE][CODE]
    errors  = check_full_coverage(draft)               # every object/attribute has a record (UNRESOLVED counts)
    errors += check_no_inferred_marked_observed(draft)
    errors += check_every_inferred_cites_evidence(draft)
    errors += check_keys_privacy_relationships_flagged(draft)
    errors += validate_json_schema(draft)              # contracts/*.schema.json

    return Result(ok = (errors == []), errors = errors)
    # Fail -> back to Phases 3-6 with these errors. A failing draft NEVER persists as reviewable.
    # [STATUS] JSON-Schema contracts ... BUILT.   The validator that runs them in this loop ... NOT BUILT.
```

## Phase 8 — Human review (the only path to APPROVED — and where memory grows)

```python
def phase8_human_review(draft):                        # [HUMAN][GATE][MEM w]
    queue = select_for_review(draft)                   # TARGETED, not exhaustive:
        # always: keys, privacy, material relationships, every INFERRED, all UNRESOLVED, contradictions
        # not queued: high-confidence OBSERVED facts (spot-check in bulk)

    for item in queue:
        decision = person.decide(item)                 # APPROVE / MODIFY / REJECT / DEFER
        if decision.is_material:
            show_impact_analysis(item)                 # before it is accepted
        save_review_decision(decision)                 # [MEM w] EPISODIC memory — this is the write that feeds Phase 0 next run

    return classify(draft, decisions)                  # APPROVED items vs still-DRAFT items
    # Nothing auto-approves.
    # [STATUS] review app ......... STUB
    #          save_review_decision  NOT WIRED  --> the memory write-path is missing (ADR-006 decision-capture gap)
```

## Phase 9 — Persist and publish (code)

```python
def phase9_persist_and_publish(review):                # [CODE][MEM w]
    save_delta(review.all_records,                     # AUTHORITATIVE source of truth
               version=..., run_id=..., provenance=...)
    regenerate_excel_from_delta()                      # consumption only — never edited & re-imported
    refresh_app_views_from_delta()                     # consumption only
    # [STATUS] tables DEFINED (DDL exists), but no runtime writes them yet.
```

---

## The one loop that makes it "smart over time"

```
Phase 8 writes review_decisions  ─────────────┐
                                              │  (durable, engagement-scoped)
Phase 0 of the NEXT run reads them back ◀──────┘
    -> the agent stops re-litigating what a human already decided
```

This feedback loop is what the charter means by "learning from approved decisions."
**It is designed but not built** — Phase 8 doesn't write and Phase 0 doesn't read. See ADR-006.

## What actually runs today vs. not

| Phase | Built? |
|---|---|
| 0 — pack selection (semantic) | ✅ built |
| 0 — prior-decision read + context envelope | ❌ not built (`context_snapshot_id = None`) |
| 1 — metadata and restricted profile evidence | ✅ built and deployed for the synthetic proof slice |
| 2 — relationship candidates | 🟡 partial |
| 3–5 — LLM analysis + critic | ❌ not built (needs an approved pack) |
| 6 — confidence | ❌ not built |
| 7 — contracts exist / validator loop | ✅ contracts · ❌ loop |
| 8 — human review + decision write | ❌ stub |
| 9 — persist / publish | ❌ not built (tables defined only) |

So today the agent is a linear, memoryless skeleton: **validate scope → snapshot metadata → select pack.** Everything that makes it an *agent* (phases 3–9) and everything that makes it *remember* (the phase 8 → phase 0 loop) is still ahead.
