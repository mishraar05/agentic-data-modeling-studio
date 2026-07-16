# ADR-003: Contract-owned structural vocabularies

**Status:** Accepted from owner direction recorded during the Increment-1 Skill refactor  
**Date:** 2026-07-16  
**Decision owner:** Solution owner

## Context

The Source Discovery contracts require stable structural terms for evidence state, evidence provenance, confidence components and lifecycle. Earlier drafts simultaneously embedded these values in JSON Schema and described them as governed-pack vocabulary. That made core validation depend on a runtime-eligible insurance pack and created contradictory ownership.

Insurance/domain terms—such as party roles, coverage families, privacy classifications and code meanings—have different ownership and vary by pack, LOB and jurisdiction.

## Decision

The following are contract-owned structural invariants:

- claim `evidence_state`;
- evidence `provenance_class`;
- confidence-component vocabulary; and
- record lifecycle families.

They are defined once in the common contract schema and referenced by record schemas.

Domain vocabulary remains governed knowledge. Records reference it by exact `pack_id`, `pack_version`, `code_set_id`, selected `code` and fingerprint. Domain values are never copied into the structural contract schema.

## Consequences

- Contract validation can run before a knowledge pack is runtime-eligible.
- Changing a structural vocabulary requires a contract version change and architecture review.
- Changing a domain code set requires a governed-pack version/fingerprint change, not a contract-schema edit.
- Context assembly must validate governed code references against the selected authorized pack.
- This ADR grants no knowledge-pack approval or runtime eligibility.
