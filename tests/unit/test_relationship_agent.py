from __future__ import annotations

from pathlib import Path

import pytest

from agentic_data_modeler.analyst import (
    RelationshipAgent,
    RelationshipAnalysis,
    RelationshipProposal,
    assemble_relationship_context,
)
from agentic_data_modeler.slice.records import Scope


ROOT = Path(__file__).resolve().parents[2]
SCOPE = Scope(lob="personal_auto", domain="policy", run_id="run-relationship-1")


OBJECTS = [
    {
        "record_id": "obj_policy", "source_snapshot_ref": "source-1",
        "evidence_item_ref": "ev_policy", "object_name": "pc_policy",
        "object_type": "TABLE", "constraint_observations": [],
    },
    {
        "record_id": "obj_driver", "source_snapshot_ref": "source-1",
        "evidence_item_ref": "ev_driver", "object_name": "pc_driver",
        "object_type": "TABLE", "constraint_observations": [],
    },
]

ATTRIBUTES = [
    {
        "record_id": "attr_policy_id", "source_snapshot_ref": "source-1",
        "evidence_item_ref": "ev_policy_id", "object_name": "pc_policy",
        "attribute_name": "ID", "ordinal_position": 1, "data_type": "BIGINT",
        "nullable": False, "constraint_role": "PRIMARY_KEY",
    },
    {
        "record_id": "attr_driver_policy", "source_snapshot_ref": "source-1",
        "evidence_item_ref": "ev_driver_policy", "object_name": "pc_driver",
        "attribute_name": "PolicyID", "ordinal_position": 2, "data_type": "BIGINT",
        "nullable": False, "constraint_role": "NONE",
    },
]

PROFILES = [
    {
        "record_id": "profile_policy_id", "evidence_item_ref": "pev_policy_id",
        "object_name": "pc_policy", "attribute_name": "ID",
        "row_count": 100, "null_count": 0, "distinct_count": 100,
    },
    {
        "record_id": "profile_driver_policy", "evidence_item_ref": "pev_driver_policy",
        "object_name": "pc_driver", "attribute_name": "PolicyID",
        "row_count": 250, "null_count": 0, "distinct_count": 100,
    },
]


class RelationshipProducer:
    def analyze_relationships(self, req):
        assert req.context_snapshot_ref == "context-1"
        assert "attr_policy_id" in req.allowed_evidence
        return RelationshipAnalysis((RelationshipProposal(
            parent_object="pc_policy", parent_attributes=("ID",),
            child_object="pc_driver", child_attributes=("PolicyID",),
            relationship_type="INFERRED_FK", relationship_name="Policy has drivers",
            cardinality="1:M", optionality="REQUIRED",
            rationale="PolicyID connects a driver row to its policy and the profiles support reuse.",
            evidence_refs=("attr_policy_id", "attr_driver_policy", "profile_policy_id", "profile_driver_policy"),
        ),))


class NoFindingCritic:
    def critique(self, req):
        assert "pc_policy" in req.draft_summary
        return []


def _context(*, prior=()):
    return assemble_relationship_context(
        lob=SCOPE.lob, domain=SCOPE.domain,
        source_snapshot_ref="source-1", evidence_set_ref="evidence-set-1",
        context_snapshot_ref="context-1", object_observations=OBJECTS,
        attribute_observations=ATTRIBUTES, profile_evidence=PROFILES,
        glossary={"Policy": "Insurance contract."}, prior_decisions=prior,
    )


def test_llm_relationship_is_grounded_critic_checked_and_reviewable():
    result = RelationshipAgent(ROOT, RelationshipProducer(), NoFindingCritic()).analyze(SCOPE, _context())

    assert result.stats["candidates"] == 1
    assert result.stats["rejected"] == 0
    candidate = result.candidates[0]
    assert candidate["lifecycle_state"] == "DRAFT"
    assert candidate["evidence_set_ref"] == "evidence-set-1"
    assert candidate["critic_status"] == "CONFIRMED"
    assert candidate["relationship_name"]["evidence_state"] == "INFERRED"
    assert set(candidate["evidence_refs"]) == {
        "attr_policy_id", "attr_driver_policy", "profile_policy_id", "profile_driver_policy"
    }
    assert len(result.review_items) == 1


def test_invalid_model_citation_fails_closed():
    class InventingProducer(RelationshipProducer):
        def analyze_relationships(self, req):
            proposal = super().analyze_relationships(req).proposals[0]
            return RelationshipAnalysis((RelationshipProposal(
                parent_object=proposal.parent_object, parent_attributes=proposal.parent_attributes,
                child_object=proposal.child_object, child_attributes=proposal.child_attributes,
                relationship_type=proposal.relationship_type, relationship_name=proposal.relationship_name,
                cardinality=proposal.cardinality, optionality=proposal.optionality,
                rationale=proposal.rationale, evidence_refs=("invented-evidence",),
            ),))

    result = RelationshipAgent(ROOT, InventingProducer()).analyze(SCOPE, _context())
    assert result.candidates == []
    assert result.stats["rejected"] == 1
    assert result.validation_findings[0]["severity"] == "ERROR"


def test_approved_relationship_memory_is_reused_without_auto_approval():
    prior = ({
        "parent_object": "pc_policy", "parent_attributes": ["ID"],
        "child_object": "pc_driver", "child_attributes": ["PolicyID"],
        "relationship_type": "INFERRED_FK", "relationship_name": "Policy has drivers",
        "cardinality": "1:M", "optionality": "REQUIRED",
        "review_decision_ref": "decision-1",
        "evidence_refs": ["attr_policy_id", "attr_driver_policy"],
    },)
    result = RelationshipAgent(ROOT, RelationshipProducer()).analyze(SCOPE, _context(prior=prior))
    candidate = result.candidates[0]
    assert candidate["lifecycle_state"] == "APPROVED"
    assert candidate["review_decision_ref"] == "decision-1"
    assert candidate["relationship_name"]["evidence_state"] == "DECIDED"
    assert result.review_items == []


def test_context_byte_budget_fails_closed_without_truncation():
    with pytest.raises(ValueError, match="byte budget"):
        assemble_relationship_context(
            lob=SCOPE.lob, domain=SCOPE.domain,
            source_snapshot_ref="source-1", evidence_set_ref="evidence-set-1",
            context_snapshot_ref="context-1", object_observations=OBJECTS,
            attribute_observations=ATTRIBUTES, glossary={"large": "x" * 1000},
            max_context_bytes=10,
        )
