"""Pluggable review policy (Phase 8).

The human approval gate is a *seam*, not deleted. ``AutoApprovePolicy`` bypasses
it for development velocity; ``HumanReviewPolicy`` is where a real reviewer UI
plugs in. Swapping the policy object restores human-in-the-loop with no other
change to the orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ReviewOutcome:
    decision: str          # APPROVE / REJECT / REVISE / DEFER
    decision_maker: str
    rationale: str


class ReviewPolicy(Protocol):
    def review(self, review_item: dict[str, Any], draft: dict[str, Any]) -> ReviewOutcome: ...

    @property
    def name(self) -> str: ...


class AutoApprovePolicy:
    """DEV ONLY — approves every item so the pipeline flows without a human."""

    name = "auto-approve(dev)"

    def review(self, review_item: dict[str, Any], draft: dict[str, Any]) -> ReviewOutcome:
        return ReviewOutcome(
            decision="APPROVE",
            decision_maker="dev-auto-approver",
            rationale="Auto-approved in development mode; human review bypassed by policy.",
        )


class HumanReviewPolicy:
    """Placeholder for the real human gate (review app / queue)."""

    name = "human"

    def review(self, review_item: dict[str, Any], draft: dict[str, Any]) -> ReviewOutcome:  # pragma: no cover
        raise NotImplementedError(
            "Wire this to the Databricks review app / decision-capture path."
        )
