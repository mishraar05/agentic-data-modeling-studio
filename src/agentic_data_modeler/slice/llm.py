"""Pluggable semantic producer (the [LLM] steps of Phases 3-4).

The interface is what a real model implements. ``DeterministicStubLLM`` is a
development placeholder: it derives *plausible* business meaning from column
names with simple heuristics so the pipeline runs offline. It is explicitly NOT
a curated answer key and makes no quality claim — replace it with a real model
(Databricks/Anthropic) implementing the same ``propose_attribute`` method.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AttributeProposal:
    sufficient: bool                      # False -> becomes UNRESOLVED + open_question
    business_name: str | None = None
    business_definition: str | None = None
    key_role: str | None = None           # PRIMARY_KEY / FOREIGN_KEY / None
    privacy_sensitive: bool = False
    glossary_hits: tuple[str, ...] = field(default_factory=tuple)


class LLM(Protocol):
    def propose_attribute(
        self, *, object_name: str, attribute_name: str, data_type: str,
        nullable: bool, constraint_role: str, glossary_terms: dict[str, str],
    ) -> AttributeProposal: ...


_ABBREV = {
    "id": "identifier", "num": "number", "amt": "amount", "dt": "date",
    "ts": "timestamp", "cd": "code", "desc": "description", "nm": "name",
    "addr": "address", "dob": "date of birth", "ssn": "social security number",
    "veh": "vehicle", "drv": "driver", "pol": "policy", "clm": "claim",
    "cov": "coverage", "prem": "premium", "eff": "effective", "exp": "expiration",
}
_PRIVACY = re.compile(r"(ssn|social_security|dob|birth|first_name|last_name|full_name|"
                      r"email|phone|address|license|passport|tax_id)", re.I)
_OPAQUE = re.compile(r"^(col|c|f|x|fld|field|val|attr)_?\d+$", re.I)


def _humanize(name: str) -> str:
    words = [w for w in re.split(r"[_\s]+", name.strip().lower()) if w]
    return " ".join(_ABBREV.get(w, w) for w in words)


class DeterministicStubLLM:
    """Heuristic stand-in for the real semantic model. Not evaluated quality."""

    def propose_attribute(
        self, *, object_name: str, attribute_name: str, data_type: str,
        nullable: bool, constraint_role: str, glossary_terms: dict[str, str],
    ) -> AttributeProposal:
        if _OPAQUE.match(attribute_name):
            return AttributeProposal(sufficient=False)  # opaque -> ask, never guess

        human = _humanize(attribute_name)
        hits = tuple(sorted(t for t in glossary_terms if t.lower() in human))
        definition = glossary_terms[hits[0]] if hits else (
            f"{human.capitalize()} on {_humanize(object_name)}."
        )
        key_role = None
        if constraint_role == "PRIMARY_KEY" or attribute_name.lower().endswith("_id"):
            key_role = "PRIMARY_KEY" if constraint_role == "PRIMARY_KEY" else "FOREIGN_KEY"
        return AttributeProposal(
            sufficient=True,
            business_name=human.title(),
            business_definition=definition,
            key_role=key_role,
            privacy_sensitive=bool(_PRIVACY.search(attribute_name)),
            glossary_hits=hits,
        )
