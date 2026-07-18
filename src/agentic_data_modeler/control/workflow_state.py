"""Deterministic work-package workflow-state rules."""

WORK_PACKAGE_WORKFLOW_STATES = (
    "VALIDATED",
    "METADATA_READY",
    "PROFILE_READY",
    "EVIDENCE_READY",
    "CONTEXT_READY",
    "SDD_READY",
    "SILVER_READY",
    "GOLD_READY",
    "STTM_READY",
    "PUBLISHED",
)


def registration_rerun_preserves_state(workflow_state: str) -> bool:
    """Return whether registration may safely reuse an existing work package.

    Registration establishes the initial ``VALIDATED`` state. A rerun may see
    that state or any governed downstream state, but it must never regress it.
    """

    return workflow_state in WORK_PACKAGE_WORKFLOW_STATES
