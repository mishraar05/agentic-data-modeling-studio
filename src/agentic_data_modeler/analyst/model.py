"""Pluggable model port for the Source Data Analyst.

The port defines what the analyst asks a model to do: given one attribute's
evidence and the governed glossary, propose a business name and definition and
declare *which* of the allowed evidence items support each. The port never
decides trust state or safety — the SA1 producer does that deterministically.

A real ``DatabricksFoundationModel`` adapter is included; it calls a Databricks
serving endpoint (OpenAI-compatible) and requires a live endpoint + token, so it
is not exercised by unit tests. Tests use a scripted double implementing the
same ``AnalystModel`` protocol.
"""

from __future__ import annotations

import json
import textwrap
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class AttributeRequest:
    object_name: str
    attribute_name: str
    data_type: str
    nullable: bool
    constraint_role: str
    observation_ref: str                    # evidence id available for this attribute
    allowed_evidence: tuple[str, ...]        # the ONLY evidence ids the model may cite
    glossary: dict[str, str] = field(default_factory=dict)
    prior_decision_ref: str | None = None    # episodic: a human already decided this
    prior_values: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class FieldProposal:
    """A proposed value plus the evidence the model claims supports it."""
    value: str | None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AttributeAnalysis:
    business_name: FieldProposal
    business_definition: FieldProposal


@dataclass(frozen=True, slots=True)
class ObjectRequest:
    object_name: str
    object_type: str
    attribute_names: tuple[str, ...]
    observation_ref: str
    allowed_evidence: tuple[str, ...]
    glossary: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ObjectAnalysis:
    business_name: FieldProposal
    business_definition: FieldProposal
    business_purpose: FieldProposal
    entity_type: FieldProposal


class AnalystModel(Protocol):
    def analyze_attribute(self, req: AttributeRequest) -> AttributeAnalysis: ...
    def analyze_object(self, req: ObjectRequest) -> ObjectAnalysis: ...
    def analyze_relationships(self, req: "RelationshipRequest") -> "RelationshipAnalysis": ...


@dataclass(frozen=True, slots=True)
class RelationshipRequest:
    """Bounded, immutable relationship-analysis context supplied to the model."""

    lob: str
    domain: str
    source_snapshot_ref: str
    evidence_set_ref: str
    context_snapshot_ref: str
    schema_inventory: tuple[dict[str, Any], ...]
    allowed_evidence: tuple[str, ...]
    glossary: dict[str, str] = field(default_factory=dict)
    prior_decisions: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class RelationshipProposal:
    parent_object: str
    parent_attributes: tuple[str, ...]
    child_object: str
    child_attributes: tuple[str, ...]
    relationship_type: str
    relationship_name: str | None
    cardinality: str | None
    optionality: str | None
    rationale: str
    evidence_refs: tuple[str, ...]
    open_question: str | None = None


@dataclass(frozen=True, slots=True)
class RelationshipAnalysis:
    proposals: tuple[RelationshipProposal, ...]


@dataclass(frozen=True, slots=True)
class CriticFinding:
    finding_text: str
    severity: str = "WARNING"              # BLOCKING | ERROR | WARNING | INFO
    finding_type: str = "CONTRADICTION"    # SCHEMA | REFERENTIAL | COVERAGE | POLICY | CONTRADICTION
    affected_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CritiqueRequest:
    draft_summary: str
    evidence_summary: str


class CriticModel(Protocol):
    """A SEPARATE model (different endpoint) that challenges the producer's drafts."""
    def critique(self, req: CritiqueRequest) -> list[CriticFinding]: ...


# --- prompt construction (SA1 rendered; the SKILL.md remains the source of truth) ---

_SYSTEM = textwrap.dedent(
    """\
    You are the Source Data Analyst (skill SA1). For ONE source attribute you
    propose a business name and a plain-language business definition.

    Hard rules:
    - Ground every proposal in the provided evidence. For each field, list the
      evidence ids (from ALLOWED_EVIDENCE only) that support your value.
    - If the evidence is insufficient to say what the attribute means, return
      null for that field and an empty evidence list. Never guess. Never invent
      an evidence id, a column, or a governed term.
    - Prefer a governed glossary match when one applies.

    Respond as JSON only:
    {"business_name": {"value": <string|null>, "evidence_refs": [<id>...]},
     "business_definition": {"value": <string|null>, "evidence_refs": [<id>...]}}
    """
)


def render_messages(req: AttributeRequest) -> list[dict[str, str]]:
    glossary = "\n".join(f"- {t}: {d}" for t, d in sorted(req.glossary.items())) or "(none)"
    user = textwrap.dedent(
        f"""\
        OBJECT: {req.object_name}
        ATTRIBUTE: {req.attribute_name}
        DATA_TYPE: {req.data_type}
        NULLABLE: {req.nullable}
        KEY_ROLE: {req.constraint_role}
        ALLOWED_EVIDENCE: {list(req.allowed_evidence)}
        GOVERNED_GLOSSARY:
        {glossary}
        """
    )
    return [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": user}]


def parse_analysis(content: str) -> AttributeAnalysis:
    """Parse a model JSON response into an AttributeAnalysis (no guardrails here)."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}") from exc

    def field_of(key: str) -> FieldProposal:
        raw = data.get(key) or {}
        value = raw.get("value")
        refs = raw.get("evidence_refs") or []
        return FieldProposal(
            value=value if isinstance(value, str) and value.strip() else None,
            evidence_refs=tuple(str(r) for r in refs),
        )

    return AttributeAnalysis(business_name=field_of("business_name"),
                             business_definition=field_of("business_definition"))


_OBJECT_SYSTEM = textwrap.dedent(
    """\
    You are the Source Data Analyst (skill SA1) analyzing one source TABLE.
    Propose its business name, definition, purpose, and entity type. For each,
    cite evidence ids from ALLOWED_EVIDENCE only. If evidence is insufficient for
    a field, return null with an empty evidence list. Never guess or invent.

    JSON only:
    {"business_name":{"value":<string|null>,"evidence_refs":[...]},
     "business_definition":{"value":<string|null>,"evidence_refs":[...]},
     "business_purpose":{"value":<string|null>,"evidence_refs":[...]},
     "entity_type":{"value":<string|null>,"evidence_refs":[...]}}
    """
)


def render_object_messages(req: "ObjectRequest") -> list[dict[str, str]]:
    glossary = "\n".join(f"- {t}: {d}" for t, d in sorted(req.glossary.items())) or "(none)"
    user = textwrap.dedent(
        f"""\
        OBJECT: {req.object_name}
        OBJECT_TYPE: {req.object_type}
        ATTRIBUTES: {list(req.attribute_names)}
        ALLOWED_EVIDENCE: {list(req.allowed_evidence)}
        GOVERNED_GLOSSARY:
        {glossary}
        """
    )
    return [{"role": "system", "content": _OBJECT_SYSTEM}, {"role": "user", "content": user}]


def parse_object_analysis(content: str) -> ObjectAnalysis:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {exc}") from exc

    def field_of(key: str) -> FieldProposal:
        raw = data.get(key) or {}
        value = raw.get("value")
        return FieldProposal(
            value=value if isinstance(value, str) and value.strip() else None,
            evidence_refs=tuple(str(r) for r in (raw.get("evidence_refs") or [])))

    return ObjectAnalysis(field_of("business_name"), field_of("business_definition"),
                          field_of("business_purpose"), field_of("entity_type"))


_RELATIONSHIP_SYSTEM = textwrap.dedent(
    """\
    You are the Source Relationship Analyst. Identify candidate relationships
    using the supplied source metadata, aggregate profiles, governed glossary,
    and prior approved decisions. Semantic judgment belongs to you; exact facts
    remain owned by the evidence records.

    Hard rules:
    - Use only objects, attributes, and evidence ids in the supplied context.
    - Do not assume that matching datatypes or an ID-like suffix proves a link.
    - A candidate must cite at least one ALLOWED_EVIDENCE id.
    - Use prior decisions as durable memory, but identify contradictory new evidence.
    - When evidence is insufficient, set the uncertain semantic fields to null and
      provide one focused open_question. Never invent source facts.
    - Nothing you return is approved.

    JSON only:
    {"relationships":[{
      "parent_object":<string>, "parent_attributes":[<string>...],
      "child_object":<string>, "child_attributes":[<string>...],
      "relationship_type":"FOREIGN_KEY|INFERRED_FK|LOOKUP|BRIDGE|SELF_REFERENCE",
      "relationship_name":<string|null>, "cardinality":<string|null>,
      "optionality":<string|null>, "rationale":<string>,
      "evidence_refs":[<allowed id>...], "open_question":<string|null>
    }]}
    """
)


def render_relationship_messages(req: "RelationshipRequest") -> list[dict[str, str]]:
    payload = {
        "scope": {"lob": req.lob, "domain": req.domain},
        "snapshots": {
            "source": req.source_snapshot_ref,
            "evidence_set": req.evidence_set_ref,
            "context": req.context_snapshot_ref,
        },
        "schema_inventory": req.schema_inventory,
        "allowed_evidence": req.allowed_evidence,
        "governed_glossary": req.glossary,
        "prior_approved_relationships": req.prior_decisions,
    }
    return [
        {"role": "system", "content": _RELATIONSHIP_SYSTEM},
        {"role": "user", "content": json.dumps(payload, sort_keys=True, default=str)},
    ]


def parse_relationship_analysis(content: str) -> RelationshipAnalysis:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Relationship model did not return valid JSON: {exc}") from exc
    proposals: list[RelationshipProposal] = []
    for raw in data.get("relationships", []):
        proposals.append(RelationshipProposal(
            parent_object=str(raw.get("parent_object", "")).strip(),
            parent_attributes=tuple(str(v) for v in (raw.get("parent_attributes") or [])),
            child_object=str(raw.get("child_object", "")).strip(),
            child_attributes=tuple(str(v) for v in (raw.get("child_attributes") or [])),
            relationship_type=str(raw.get("relationship_type", "INFERRED_FK")).upper(),
            relationship_name=_optional_text(raw.get("relationship_name")),
            cardinality=_optional_text(raw.get("cardinality")),
            optionality=_optional_text(raw.get("optionality")),
            rationale=str(raw.get("rationale", "")).strip(),
            evidence_refs=tuple(str(v) for v in (raw.get("evidence_refs") or [])),
            open_question=_optional_text(raw.get("open_question")),
        ))
    return RelationshipAnalysis(tuple(proposals))


def _optional_text(value: Any) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


_CRITIC_SYSTEM = textwrap.dedent(
    """\
    You are an INDEPENDENT critic (skill CR1) reviewing another model's draft
    Source Data Dictionary. Challenge: inferences not supported by the cited
    evidence, the same name defined inconsistently across objects, coverage gaps,
    and policy violations. Do not rewrite the draft; only raise findings.

    JSON only:
    {"findings":[{"finding_text":<string>,"severity":"BLOCKING|ERROR|WARNING|INFO",
                  "finding_type":"SCHEMA|REFERENTIAL|COVERAGE|POLICY|CONTRADICTION",
                  "affected_refs":[...]}]}
    """
)


def render_critic_messages(req: "CritiqueRequest") -> list[dict[str, str]]:
    user = f"DRAFTS:\n{req.draft_summary}\n\nEVIDENCE:\n{req.evidence_summary}\n"
    return [{"role": "system", "content": _CRITIC_SYSTEM}, {"role": "user", "content": user}]


def parse_findings(content: str) -> list[CriticFinding]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Critic did not return valid JSON: {exc}") from exc
    out = []
    for f in data.get("findings", []):
        out.append(CriticFinding(
            finding_text=str(f.get("finding_text", "")).strip() or "(unspecified)",
            severity=str(f.get("severity", "WARNING")).upper(),
            finding_type=str(f.get("finding_type", "CONTRADICTION")).upper(),
            affected_refs=tuple(str(r) for r in (f.get("affected_refs") or []))))
    return out


class DatabricksFoundationModel:
    """Real adapter for a Databricks serving endpoint.

    Uses Databricks SDK default notebook authentication; not used in unit tests. Example:
        model = DatabricksFoundationModel("databricks-meta-llama-3-3-70b-instruct")
    A host/token may be supplied for local use, but notebook jobs do not persist secrets.
    """

    def __init__(self, endpoint: str, *, host: str | None = None,
                 token: str | None = None, temperature: float = 0.0):
        self.endpoint = endpoint
        self.host = host
        self.token = token
        self.temperature = temperature

    def _complete(self, messages):  # pragma: no cover
        from databricks.sdk import WorkspaceClient
        from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

        roles = {
            "system": ChatMessageRole.SYSTEM,
            "user": ChatMessageRole.USER,
            "assistant": ChatMessageRole.ASSISTANT,
        }
        client = WorkspaceClient(host=self.host, token=self.token) if self.host else WorkspaceClient()
        response = client.serving_endpoints.query(
            name=self.endpoint,
            temperature=self.temperature,
            max_tokens=4096,
            messages=[ChatMessage(role=roles[item["role"]], content=item["content"])
                      for item in messages],
        )
        if not response.choices or len(response.choices) != 1:
            raise ValueError("Serving endpoint returned no single chat completion")
        message = response.choices[0].message
        if message is None or not message.content:
            raise ValueError("Serving endpoint returned an empty chat completion")
        return message.content

    def analyze_attribute(self, req: AttributeRequest) -> AttributeAnalysis:  # pragma: no cover
        return parse_analysis(self._complete(render_messages(req)))

    def analyze_object(self, req: ObjectRequest) -> ObjectAnalysis:  # pragma: no cover
        return parse_object_analysis(self._complete(render_object_messages(req)))

    def analyze_relationships(self, req: RelationshipRequest) -> RelationshipAnalysis:  # pragma: no cover
        return parse_relationship_analysis(self._complete(render_relationship_messages(req)))

    def critique(self, req: CritiqueRequest) -> list[CriticFinding]:  # pragma: no cover
        return parse_findings(self._complete(render_critic_messages(req)))
