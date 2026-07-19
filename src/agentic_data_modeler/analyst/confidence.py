"""Evidence-based confidence (Phase 6).

Confidence is reported as its components, derived from real signals — NOT a
calibrated probability. It stays a triage signal until scored on graded examples
(Charter §7). The critic pass then records whether an independent model confirmed
or contested each inferred claim.
"""

from __future__ import annotations

from typing import Any


def glossary_hit(text: str, glossary: dict[str, str]) -> bool:
    low = (text or "").lower().replace("_", " ")
    return any(term.lower() in low for term in glossary)


def derive_confidence(*, evidence_refs: list[str], constraint_role: str = "NONE",
                      is_glossary_hit: bool = False) -> dict[str, Any]:
    if constraint_role and constraint_role != "NONE":
        evidence_type = "DECLARED_CONSTRAINT"          # backed by a real key/constraint
    elif is_glossary_hit:
        evidence_type = "GLOSSARY_MATCH"               # matched governed vocabulary
    else:
        evidence_type = "SINGLE_LLM_INFERENCE"         # only the model's judgment
    return {"evidence_type": evidence_type,
            "evidence_count": max(1, len(evidence_refs)),
            "critic_agreement": "NOT_ASSESSED"}


def apply_critic_agreement(records: list[dict[str, Any]], findings: list[dict[str, Any]],
                           *, claim_fields: list[str]) -> int:
    """Set critic_agreement CONTESTED for records a finding references, else CONFIRMED,
    on INFERRED claims. Enum-safe in-place update; returns how many claims changed."""
    contested = {r for f in findings for r in (f.get("affected_record_refs") or [])}
    changed = 0
    for rec in records:
        agree = "CONTESTED" if rec["record_id"] in contested else "CONFIRMED"
        for field in claim_fields:
            claim = rec.get(field)
            if isinstance(claim, dict) and claim.get("evidence_state") == "INFERRED" and "confidence" in claim:
                claim["confidence"]["critic_agreement"] = agree
                changed += 1
    return changed
