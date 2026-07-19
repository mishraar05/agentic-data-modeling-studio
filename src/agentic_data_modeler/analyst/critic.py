"""CR1 — independent critic (Phase 5), run on a SEPARATE model.

Challenges the producer's drafts and emits validation_finding records. Using a
different model + reduced context is what makes agreement meaningful rather than
correlated (ADR-005 F1). The critic never rewrites drafts — it only raises findings.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import records as AR
from ..slice.records import Scope
from .model import CriticModel, CritiqueRequest

_FINDING_TYPES = {"SCHEMA", "REFERENTIAL", "COVERAGE", "POLICY", "CONTRADICTION"}
_SEVERITIES = {"BLOCKING", "ERROR", "WARNING", "INFO"}


def _value(claim: dict[str, Any]) -> str:
    return f"{claim.get('value', '(unresolved)')} [{claim['evidence_state']}]"


class Critic:
    def __init__(self, repo_root: str | Path, critic_model: CriticModel):
        self.root = Path(repo_root)
        self.model = critic_model

    def review(self, scope: Scope, *, artifact_version_ref: str,
               dictionary_attributes: list[dict[str, Any]],
               dictionary_objects: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        summary = self._summarize(dictionary_attributes, dictionary_objects or [])
        findings = self.model.critique(CritiqueRequest(
            draft_summary=summary, evidence_summary="(evidence ids are cited inside each draft)"))
        out: list[dict[str, Any]] = []
        for f in findings:
            out.append(AR.validation_finding(
                self.root, scope, artifact_version_ref=artifact_version_ref,
                finding_type=f.finding_type if f.finding_type in _FINDING_TYPES else "CONTRADICTION",
                severity=f.severity if f.severity in _SEVERITIES else "WARNING",
                finding_text=f.finding_text, affected_record_refs=list(f.affected_refs) or None))
        return out

    @staticmethod
    def _summarize(attrs: list[dict], objs: list[dict]) -> str:
        lines = []
        for o in objs:
            lines.append(f"OBJECT {o['source_object_name']}: name={_value(o['business_name'])}")
        for a in attrs:
            lines.append(f"ATTR {a['source_object_name']}.{a['source_attribute_name']}: "
                         f"name={_value(a['business_name'])} def={_value(a['business_definition'])}")
        return "\n".join(lines)
