# Source and provenance policy

## Source tiers

| Tier | Examples | Default use |
|---|---|---|
| Official primary | Statutes, regulations, regulator orders, official standards/APIs | Structured fact citation or independent paraphrase with section/effective date |
| Official explanatory | Regulator consumer/industry guidance | Cite and identify as guidance, not binding law |
| Public industry reference | Public NAIC/industry glossary or reporting instructions | Link and independently paraphrase; record usage/licensing review when copyrighted |
| Licensed proprietary | Forms, manuals, classifications, vendor models | Admit only with recorded entitlement and permitted storage/use |
| Enterprise confidential | Carrier manuals, code sets, decisions | Enterprise extension only; never public reusable pack |
| Secondary | Commentary, articles, aggregators | Discovery/corroboration only; do not anchor a material jurisdiction rule when primary authority exists |

## Provenance rules

- Register every source before citing it.
- Record stable source ID, publisher, URL/path, source class, applicability, usage basis and verification date.
- Cite every material claim at claim level. Module-level references are an index, not sufficient provenance for new packs.
- Record the exact section/page/paragraph for thresholds, dates, obligations, formulae and definitions when available.
- Separate observed text/fact, independent paraphrase, modeling inference and human decision.
- Preserve effective-from/effective-to and supersession state. If unknown, mark unresolved.
- Retain contradictions; do not select the convenient source silently.
- Prefer concise original wording and structured fields. Do not reproduce full documents or substantial protected text.

## Usage-rights handling

- `public_statute_structured_fact_citation`: store structured facts/citations, not vendor editorial material.
- `link_and_independent_paraphrase`: link to the source and use original concise wording.
- `pending_licensing_review`: keep the pack candidate and do not redistribute protected content.
- `licensed_internal_use`: require entitlement reference, permitted users/purpose and storage restrictions.
- `client_confidential`: isolate to an authorized enterprise/client extension.

Do not treat public web access as a redistribution licence. Escalate unclear terms to the content owner; escalate ambiguous high-impact legal interpretation to the appropriate compliance/legal reviewer.

## Research stop conditions

Stop and record a gap when:

- no authoritative source supports a material claim;
- sources conflict and applicability cannot be resolved;
- current/effective version cannot be established;
- usage rights do not permit the intended storage or distribution;
- the only source is proprietary and authorization is absent; or
- the requested content would expose client data, PII, credentials or restricted material.

