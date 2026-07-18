"""Runnable Source Data Dictionary vertical slice.

This package wires Phases 0-9 of the SDD agent end to end so the design can be
exercised against synthetic data. It is a development slice, not production:

- the semantic producer is a pluggable ``LLM`` (a deterministic stub today);
- human review is a pluggable ``ReviewPolicy`` (``AutoApprove`` in dev, so the
  gate is bypassed, not deleted); and
- persistence and memory are local JSON stores standing in for Delta tables.

Every record it emits validates against the real ``contracts/*.schema.json``.
Swap the stub LLM, the review policy, and the stores for real implementations
to move from slice to product without changing the orchestration.
"""

__all__ = ["orchestrator"]
