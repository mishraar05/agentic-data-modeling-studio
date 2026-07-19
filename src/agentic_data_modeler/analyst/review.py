"""Human review preparation (Phase 8, human-approval path).

Prepares review_item records so a person can approve/modify/reject/defer. It
NEVER auto-approves and never writes a review_decision — approval is a human act.
Every non-DECIDED draft becomes a review item; findings are surfaced too.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..slice import records as R
from ..slice.records import Scope


def prepare_review_items(root: str | Path, scope: Scope, *,
                         dictionary_objects: list[dict[str, Any]],
                         dictionary_attributes: list[dict[str, Any]],
                         validation_findings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    root = Path(root)
    items: list[dict[str, Any]] = []

    for o in dictionary_objects:
        if o["lifecycle_state"] == "APPROVED":       # already a prior human decision
            continue
        items.append(R.review_item(
            root, scope, artifact_version_ref=o["record_id"],
            review_question=f"Approve table meaning for {o['source_object_name']} "
                            f"(name is {o['business_name']['evidence_state']}). Not auto-approved."))

    for a in dictionary_attributes:
        if a["lifecycle_state"] == "APPROVED":
            continue
        items.append(R.review_item(
            root, scope, artifact_version_ref=a["record_id"],
            review_question=f"Approve column meaning for {a['source_object_name']}."
                            f"{a['source_attribute_name']} "
                            f"(name is {a['business_name']['evidence_state']}). Not auto-approved."))

    for f in validation_findings or []:
        items.append(R.review_item(
            root, scope, artifact_version_ref=f["record_id"],
            review_question=f"Critic finding ({f['severity']}/{f['finding_type']}): {f['finding_text']}"))

    return items
