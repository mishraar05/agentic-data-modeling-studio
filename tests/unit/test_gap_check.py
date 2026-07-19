"""Deterministic gap/contradiction detector (Phase 5 code half)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentic_data_modeler.analyst.gap_check import run_gap_checks
from agentic_data_modeler.slice.records import Scope

SCOPE = Scope(lob="personal_auto", domain="policy", run_id="RUN-1")


def _da(record_id, obj, attr, definition):
    return {"record_id": record_id, "source_object_name": obj, "source_attribute_name": attr,
            "business_name": {"value": attr.title(), "evidence_state": "INFERRED"},
            "business_definition": {"value": definition, "evidence_state": "INFERRED"}}


def _obs(obj, attr):
    return {"object_name": obj, "attribute_name": attr}


def test_coverage_gap_is_blocking():
    findings = run_gap_checks(
        ROOT, SCOPE, artifact_version_ref="ctx_1",
        dictionary_attributes=[_da("d1", "policy", "pol_id", "The policy id.")],
        attribute_observations=[_obs("policy", "pol_id"), _obs("policy", "premium_amt")])
    cov = [f for f in findings if f["finding_type"] == "COVERAGE"]
    assert len(cov) == 1 and cov[0]["severity"] == "BLOCKING"
    assert "premium_amt" in cov[0]["finding_text"]


def test_conflicting_definitions_flagged():
    findings = run_gap_checks(
        ROOT, SCOPE, artifact_version_ref="ctx_1",
        dictionary_attributes=[
            _da("d1", "policy", "status", "Whether the policy is active."),
            _da("d2", "claim", "status", "The stage of the claim lifecycle.")],
        attribute_observations=[_obs("policy", "status"), _obs("claim", "status")])
    contra = [f for f in findings if f["finding_type"] == "CONTRADICTION"]
    assert len(contra) == 1
    assert set(contra[0]["affected_record_refs"]) == {"d1", "d2"}


def test_consistent_definitions_no_contradiction():
    findings = run_gap_checks(
        ROOT, SCOPE, artifact_version_ref="ctx_1",
        dictionary_attributes=[
            _da("d1", "policy", "status", "Lifecycle status."),
            _da("d2", "claim", "status", "Lifecycle status.")],
        attribute_observations=[_obs("policy", "status"), _obs("claim", "status")])
    assert [f for f in findings if f["finding_type"] == "CONTRADICTION"] == []
