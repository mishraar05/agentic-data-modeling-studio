# Architecture

Solution architecture for the Agentic Data Analyst and Modeler. Governed by [`../requirements/REQUIREMENTS_CHARTER.md`](../requirements/REQUIREMENTS_CHARTER.md); if any document here conflicts with the charter, the charter wins.

## Cross-cutting (this folder)

- [`AGENT_SOLUTION_ARCHITECTURE.md`](AGENT_SOLUTION_ARCHITECTURE.md) — controlling solution architecture: capabilities, LLM/code split, context contract, guardrails, harness, and skill criteria. The hub every design below elaborates.
- [`SKILL_MAP.md`](SKILL_MAP.md) — solution-wide skill inventory: which reasoning tasks become skills, their §7 declaration fields, and the anti-sprawl register of what stays code/tool/validator/context.

## Per-deliverable designs (subfolders)

- [`source-data-dictionary/`](source-data-dictionary/) — reconstructing the Source Data Dictionary: the source-discovery orchestration flow and the Source Data Analyst component design.
- [`target-modeling/`](target-modeling/) — downstream Silver ODS, Gold dimensional model, and STTM flow that consumes an approved dictionary handoff.

New deliverable areas get their own subfolder here; cross-cutting architecture and the skill map stay at the root.
