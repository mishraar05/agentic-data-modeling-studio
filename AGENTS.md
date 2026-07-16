# Agent Instructions — Current Workspace

Before planning or changing this solution, read `docs/requirements/REQUIREMENTS_CHARTER.md` and `docs/architecture/AGENT_SOLUTION_ARCHITECTURE.md` completely.

Document precedence is:

1. `docs/requirements/REQUIREMENTS_CHARTER.md` — business goal, scope, deliverables, constraints, and acceptance;
2. approved deliverable contracts;
3. `docs/architecture/AGENT_SOLUTION_ARCHITECTURE.md` — agent, technology, context, guardrail, harness, and skill decisions;
4. evaluation and acceptance plans;
5. implementation plans and code.

## Controlling direction

- The product is an Agentic Data Analyst and Modeler that creates a reconstructed Source Data Dictionary, Silver ODS model, Gold dimensional model, and STTMs by selected LOB/domain.
- Ontology is a governed input, never a solution deliverable.
- Tool-specific ETL/BI conversion is deferred but must remain addable through adapters.
- Use LLMs for semantic analysis and modeling judgment. Do not hard-code expected semantic answers to simulate determinism.
- Use deterministic code for security, state, exact calculations, contracts, validation, and policy enforcement.
- Delta records are authoritative; Excel and the Databricks App are review/consumption formats.
- A capability becomes a separate agent only when it requires a distinct authority, context, lifecycle, scale, or evaluation boundary. Otherwise prefer a reusable `SKILL.md` within the custom harness.

## Anti-drift gate

Every work item must name:

1. the Requirements Charter deliverable it advances;
2. the selected LOB/domain or reusable cross-cutting need;
3. the evidence and acceptance measure; and
4. why the work belongs now rather than in deferred extensibility.

Do not mark a phase complete from artifact counts or unit tests alone.

