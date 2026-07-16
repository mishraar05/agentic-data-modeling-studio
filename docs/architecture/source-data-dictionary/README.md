# Source Data Dictionary

Architecture for the **Reconstructed Source Data Dictionary** deliverable (Charter §5.1) — from source registration and profiling through evidence-cited reconstruction, review, approval, and handoff to downstream modeling.

- [`SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md`](SOURCE_DEPENDENT_DATABRICKS_FLOW_DESIGN.md) — orchestration-level flow: Lakeflow phases, state machine, tools/adapters, guardrails, evaluation strategy, and the `source_dictionary_handoff` contract.
- [`SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md`](SOURCE_DATA_DICTIONARY_AGENT_DESIGN.md) — component design for the Source Data Analyst capability: Phases 0–9, inputs/outputs, per-phase guardrails, and open dependencies.
- [`INCREMENT_1_CONTRACTS_GENIE_CODE_BUILD_HANDOFF.md`](INCREMENT_1_CONTRACTS_GENIE_CODE_BUILD_HANDOFF.md) — Genie Code build handoff for the Increment-1 contract suite: the 31-record schema build order, validator obligations, quality gates, and stop conditions.
- [`INCREMENT_2_SOURCE_ONBOARDING_IMPLEMENTATION_SPEC.md`](INCREMENT_2_SOURCE_ONBOARDING_IMPLEMENTATION_SPEC.md) — implementation-ready specification for authorized metadata capture, controlled profiling, supplied-evidence normalization, and the `EVIDENCE_READY` gate.
- [`INCREMENT_3_CONTEXT_ASSEMBLY_IMPLEMENTATION_SPEC.md`](INCREMENT_3_CONTEXT_ASSEMBLY_IMPLEMENTATION_SPEC.md) — implementation-ready specification for exact governed-knowledge selection, scoped evidence/decision retrieval, immutable context snapshots, and the `CONTEXT_READY` gate.
- [`INCREMENT_2_3_HUMAN_DECISION_REGISTER.md`](INCREMENT_2_3_HUMAN_DECISION_REGISTER.md) — human-owned decisions that block build, integration, or production acceptance.
- [`INCREMENT_2_3_GENIE_CODE_BUILD_HANDOFF.md`](INCREMENT_2_3_GENIE_CODE_BUILD_HANDOFF.md) — sequenced build packages, quality gates, evidence expectations, and stop conditions for Genie Code.

The flow document is the outer altitude; the component design elaborates its dictionary-reconstruction phase. The Increment 2–3 specifications stop before semantic reconstruction and consume, but do not redefine, the Increment-1 contracts. All are governed by [`../AGENT_SOLUTION_ARCHITECTURE.md`](../AGENT_SOLUTION_ARCHITECTURE.md) and the Charter.
