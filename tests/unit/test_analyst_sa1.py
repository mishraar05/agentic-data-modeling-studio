"""Harness guardrail tests for the Source Data Analyst (SA1).

Uses a scripted model double (no live model) to prove the deterministic rules:
citations required for INFERRED, invented evidence stripped, insufficient ->
UNRESOLVED + open_question, prior decisions reused as DECIDED, 100% coverage.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentic_data_modeler.analyst.model import AttributeAnalysis, AttributeRequest, FieldProposal
from agentic_data_modeler.analyst.sa1 import SourceDataAnalyst
from agentic_data_modeler.slice.records import Scope


class ScriptedModel:
    """Test double: canned proposals keyed by attribute name. Records calls."""

    def __init__(self):
        self.calls: list[str] = []

    def analyze_attribute(self, req: AttributeRequest) -> AttributeAnalysis:
        self.calls.append(req.attribute_name)
        ev = req.observation_ref
        if req.attribute_name == "premium_amt":            # well supported -> INFERRED
            return AttributeAnalysis(
                FieldProposal("Premium Amount", (ev,)),
                FieldProposal("Premium charged on the policy.", (ev,)))
        if req.attribute_name == "col_9":                  # opaque -> UNRESOLVED
            return AttributeAnalysis(FieldProposal(None, ()), FieldProposal(None, ()))
        if req.attribute_name == "sneaky":                 # value but INVENTED citation
            return AttributeAnalysis(
                FieldProposal("Made Up", ("FAKE_EVIDENCE_ID",)),
                FieldProposal("Fabricated definition.", ("FAKE_EVIDENCE_ID",)))
        return AttributeAnalysis(FieldProposal(None, ()), FieldProposal(None, ()))


def _obs(name, ordinal, dtype="STRING", nullable=True, role="NONE"):
    return {"record_id": f"obs_{name}", "object_name": "policy", "attribute_name": name,
            "ordinal_position": ordinal, "data_type": dtype, "nullable": nullable,
            "constraint_role": role}


def _state(rec, field):
    return rec[field]["evidence_state"]


def test_guardrails_over_model_output():
    model = ScriptedModel()
    analyst = SourceDataAnalyst(ROOT, model)
    scope = Scope(lob="personal_auto", domain="personal_auto_policy_claims", run_id="RUN-1")
    obs = [_obs("premium_amt", 1, "DECIMAL"), _obs("col_9", 2), _obs("sneaky", 3)]

    r = analyst.analyze_attributes(scope, context_snapshot_ref="ctx_1", attribute_observations=obs)

    # coverage: one record per attribute
    assert len(r.dictionary_attributes) == 3
    assert (r.n_inferred, r.n_unresolved, r.n_decided) == (1, 2, 0)

    by = {d["source_attribute_name"]: d for d in r.dictionary_attributes}
    # supported attribute -> INFERRED with a real citation + confidence
    assert _state(by["premium_amt"], "business_name") == "INFERRED"
    assert by["premium_amt"]["business_name"]["evidence_refs"] == ["obs_premium_amt"]
    assert "confidence" in by["premium_amt"]["business_name"]
    # opaque -> UNRESOLVED, no value, has an open question
    assert _state(by["col_9"], "business_name") == "UNRESOLVED"
    assert "value" not in by["col_9"]["business_name"]
    # invented citation stripped -> cannot become INFERRED
    assert _state(by["sneaky"], "business_name") == "UNRESOLVED"
    blob = str(r.dictionary_attributes)
    assert "FAKE_EVIDENCE_ID" not in blob and "Made Up" not in blob
    # two open questions raised (col_9, sneaky)
    assert len(r.open_questions) == 2


def test_prior_decision_reused_without_calling_model():
    model = ScriptedModel()
    analyst = SourceDataAnalyst(ROOT, model)
    scope = Scope(lob="personal_auto", domain="personal_auto_policy_claims", run_id="RUN-2")
    obs = [_obs("premium_amt", 1, "DECIMAL")]
    prior = {"default::policy::premium_amt": {
        "review_decision_ref": "rd_123",
        "values": {"business_name": "Premium Amount", "business_definition": "Approved definition."}}}

    r = analyst.analyze_attributes(scope, context_snapshot_ref="ctx_1",
                                   attribute_observations=obs, prior=prior)

    assert r.n_decided == 1 and r.n_inferred == 0
    rec = r.dictionary_attributes[0]
    assert rec["business_name"]["evidence_state"] == "DECIDED"
    assert rec["lifecycle_state"] == "APPROVED"
    assert rec["review_decision_ref"] == "rd_123"
    assert model.calls == []          # memory short-circuited the model entirely
