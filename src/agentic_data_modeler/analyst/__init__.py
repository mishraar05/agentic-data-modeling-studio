"""Source Data Analyst — the semantic producer (Phases 3-5) + human review prep.

Turns Phase-1 evidence + governed context into contract-valid Source Data
Dictionary claims by executing SA1/SA3 through a pluggable model, checked by an
independent critic (CR1) on a separate model. The harness deterministically
enforces the guardrails (no INFERRED without a citation, no invented evidence,
UNRESOLVED-not-guessing, privacy routed to a steward, 100% coverage, nothing
auto-approved) so unsafe model output can never become an approved claim.
"""

from .critic import Critic
from .model import (
    AnalystModel, AttributeAnalysis, AttributeRequest, CriticFinding, CriticModel,
    CritiqueRequest, FieldProposal, ObjectAnalysis, ObjectRequest,
    RelationshipAnalysis, RelationshipProposal, RelationshipRequest,
)
from .orchestrator import SourceDictionaryDraft, analyze_source
from .relationships import (
    RelationshipAgent, RelationshipContext, RelationshipDraft,
    assemble_relationship_context,
)
from .sa1 import AnalystResult, SourceDataAnalyst

__all__ = [
    "AnalystModel", "CriticModel", "AttributeRequest", "AttributeAnalysis",
    "ObjectRequest", "ObjectAnalysis", "FieldProposal", "CritiqueRequest", "CriticFinding",
    "RelationshipRequest", "RelationshipProposal", "RelationshipAnalysis",
    "SourceDataAnalyst", "AnalystResult", "Critic",
    "analyze_source", "SourceDictionaryDraft",
    "RelationshipAgent", "RelationshipContext", "RelationshipDraft",
    "assemble_relationship_context",
]
