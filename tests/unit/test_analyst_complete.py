"""Tests for episodic reuse, SA2 persistence, and evidence-based confidence."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentic_data_modeler.analyst.confidence import apply_critic_agreement, derive_confidence
from agentic_data_modeler.analyst.episodic import build_prior
from agentic_data_modeler.analyst.model import AttributeAnalysis, FieldProposal
from agentic_data_modeler.analyst.sa1 import SourceDataAnalyst
from agentic_data_modeler.analyst.sa2 import code_value_records
from agentic_data_modeler.slice.records import Scope

SCOPE = Scope(lob="personal_auto", domain="policy", run_id="RUN-1", memory_partition="cat.sch")
GCR = {"pack_id": "public_us_pnc_personal_auto", "pack_version": "0.6.0",
       "code_set_id": "policy_status", "fingerprint": "a" * 64, "code": "A"}


class CallModel:
    def __init__(self):
        self.calls: list[str] = []

    def analyze_attribute(self, req):
        self.calls.append(req.attribute_name)
        ev = req.observation_ref
        return AttributeAnalysis(FieldProposal("Fresh Name", (ev,)), FieldProposal("Fresh def.", (ev,)))


def _obs(name, ordinal, role="NONE"):
    return {"record_id": f"obs_{name}", "object_name": "policy", "attribute_name": name,
            "ordinal_position": ordinal, "data_type": "STRING", "nullable": True, "constraint_role": role}


# --- 1. episodic ---

def test_build_prior_approved_beats_draft():
    rows = [
        {"source_object_name": "policy", "source_attribute_name": "pol_id", "lifecycle_state": "DRAFT",
         "business_name": {"value": "Pol Id"}, "business_definition": {"value": "d"}},
        {"source_object_name": "policy", "source_attribute_name": "pol_id", "lifecycle_state": "APPROVED",
         "review_decision_ref": "rd1", "business_name": {"value": "Policy Identifier"}, "business_definition": {"value": "d"}},
        {"source_object_name": "policy", "source_attribute_name": "premium_amt", "lifecycle_state": "DRAFT",
         "business_name": {"value": "Premium"}, "business_definition": {"value": "d"}},
    ]
    prior = build_prior(rows, "cat.sch")
    assert prior["cat.sch::policy::pol_id"]["kind"] == "APPROVED"
    assert prior["cat.sch::policy::premium_amt"]["kind"] == "DRAFT"


def test_prior_draft_reused_without_calling_model():
    model = CallModel()
    analyst = SourceDataAnalyst(ROOT, model)
    prior = {"cat.sch::policy::premium_amt": {"kind": "DRAFT",
             "values": {"business_name": "Premium Amount", "business_definition": "Approved-ish."}}}
    r = analyst.analyze_attributes(SCOPE, context_snapshot_ref="ctx",
                                   attribute_observations=[_obs("premium_amt", 1)], prior=prior)
    rec = r.dictionary_attributes[0]
    assert rec["business_name"]["evidence_state"] == "INFERRED"        # carried forward, not DECIDED
    assert rec["lifecycle_state"] == "DRAFT"
    assert "Carried forward" in rec["notes"]
    assert r.n_reused_draft == 1 and model.calls == []                 # model never called


# --- 2. SA2 persistence ---

def test_code_value_records_maps_and_flags_unmapped():
    recs, unmapped = code_value_records(
        ROOT, SCOPE, context_snapshot_ref="ctx", attribute_ref="attr_1", evidence_item_ref="ev_1",
        distribution={"A": 10, "Z": 2}, code_set={"A": {"meaning": "Active", "governed_code_ref": GCR}})
    assert unmapped == ["Z"]
    assert len(recs) == 1
    assert recs[0]["code"] == "A" and recs[0]["frequency"] == 10
    assert recs[0]["governed_code_ref"] == GCR
    assert recs[0]["meaning"]["evidence_state"] == "INFERRED"


# --- 3. evidence-based confidence ---

def test_confidence_reflects_evidence():
    assert derive_confidence(evidence_refs=["e1"], constraint_role="PRIMARY_KEY")["evidence_type"] == "DECLARED_CONSTRAINT"
    g = derive_confidence(evidence_refs=["e1", "e2"], is_glossary_hit=True)
    assert g["evidence_type"] == "GLOSSARY_MATCH" and g["evidence_count"] == 2
    assert derive_confidence(evidence_refs=[])["evidence_type"] == "SINGLE_LLM_INFERENCE"


def test_critic_agreement_marks_contested_and_confirmed():
    r1 = {"record_id": "r1", "business_name": {"evidence_state": "INFERRED", "confidence": {"critic_agreement": "NOT_ASSESSED"}}}
    r2 = {"record_id": "r2", "business_name": {"evidence_state": "INFERRED", "confidence": {"critic_agreement": "NOT_ASSESSED"}}}
    apply_critic_agreement([r1, r2], [{"affected_record_refs": ["r1"]}], claim_fields=["business_name"])
    assert r1["business_name"]["confidence"]["critic_agreement"] == "CONTESTED"
    assert r2["business_name"]["confidence"]["critic_agreement"] == "CONFIRMED"
