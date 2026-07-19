"""Full Source Data Analyst flow: objects + attributes + SA3 + critic + review prep."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentic_data_modeler.analyst import analyze_source
from agentic_data_modeler.analyst.model import (
    AttributeAnalysis, CriticFinding, FieldProposal, ObjectAnalysis)
from agentic_data_modeler.slice.records import Scope


class ScriptedProducer:
    def analyze_attribute(self, req):
        ev = req.observation_ref
        if req.attribute_name == "col_9":                       # opaque -> UNRESOLVED
            return AttributeAnalysis(FieldProposal(None, ()), FieldProposal(None, ()))
        return AttributeAnalysis(
            FieldProposal(req.attribute_name.replace("_", " ").title(), (ev,)),
            FieldProposal(f"The {req.attribute_name} on {req.object_name}.", (ev,)))

    def analyze_object(self, req):
        ev = req.observation_ref
        return ObjectAnalysis(
            FieldProposal(req.object_name.title(), (ev,)),
            FieldProposal(f"Records for {req.object_name}.", (ev,)),
            FieldProposal("Operational table.", (ev,)),
            FieldProposal(None, ()))                            # entity_type -> UNRESOLVED (no governed code)


class ScriptedCritic:
    def critique(self, req):
        return [CriticFinding("A business name appears defined inconsistently.",
                              "WARNING", "CONTRADICTION", ())]


def _obj(name):
    return {"record_id": f"objobs_{name}", "object_name": name, "object_type": "TABLE",
            "evidence_item_ref": f"ev_{name}"}


def _attr(obj, name, ordinal, role="NONE"):
    return {"record_id": f"attrobs_{obj}_{name}", "object_name": obj, "attribute_name": name,
            "ordinal_position": ordinal, "data_type": "STRING", "nullable": True,
            "constraint_role": role}


SCOPE = Scope(lob="personal_auto", domain="personal_auto_policy_claims", run_id="RUN-1")
OBJECTS = [_obj("policy")]
ATTRS = [_attr("policy", "pol_id", 1, "PRIMARY_KEY"), _attr("policy", "premium_amt", 2),
         _attr("policy", "driver_ssn", 3), _attr("policy", "col_9", 4)]


def test_full_flow_with_critic_and_review():
    draft = analyze_source(
        ROOT, SCOPE, context_snapshot_ref="ctx_1",
        object_observations=OBJECTS, attribute_observations=ATTRS,
        producer_model=ScriptedProducer(), critic_model=ScriptedCritic())

    # one object with all 4 attribute refs
    assert len(draft.dictionary_objects) == 1
    assert len(draft.dictionary_objects[0]["attribute_refs"]) == 4
    assert len(draft.dictionary_attributes) == 4

    # SA3: driver_ssn flagged + routed to steward
    assert draft.stats["privacy_flagged"] == 1
    ssn = next(a for a in draft.dictionary_attributes if a["source_attribute_name"] == "driver_ssn")
    assert "privacy_steward" in ssn["notes"]
    assert ssn["open_question_refs"]

    # opaque col_9 -> UNRESOLVED, never guessed
    col9 = next(a for a in draft.dictionary_attributes if a["source_attribute_name"] == "col_9")
    assert col9["business_name"]["evidence_state"] == "UNRESOLVED"

    # critic produced a finding; review items cover objects + attributes + finding
    assert len(draft.validation_findings) == 1
    assert len(draft.review_items) == 1 + 4 + 1
    # nothing auto-approved
    assert all(o["lifecycle_state"] == "DRAFT" for o in draft.dictionary_objects)
    assert all(a["lifecycle_state"] == "DRAFT" for a in draft.dictionary_attributes)
    assert all(ri["lifecycle_state"] == "OPEN" for ri in draft.review_items)


def test_no_critic_means_no_findings():
    draft = analyze_source(
        ROOT, SCOPE, context_snapshot_ref="ctx_1",
        object_observations=OBJECTS, attribute_observations=ATTRS,
        producer_model=ScriptedProducer(), critic_model=None)
    assert draft.validation_findings == []
    assert len(draft.review_items) == 1 + 4          # objects + attributes only
