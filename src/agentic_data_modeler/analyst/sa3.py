"""SA3 signal detector — deterministic privacy/sensitivity screening.

Detects a privacy signal from the attribute name/type (never from raw values).
A positive signal routes the attribute to a privacy steward; SA3 never finalizes
a class and never fabricates a governed privacy code.
"""

from __future__ import annotations

import re

_PRIVACY = re.compile(
    r"(ssn|social_security|nation(al)?_id|tax_id|passport|driver.?licen|licen[cs]e_?no|"
    r"dob|birth|first_?name|last_?name|full_?name|sur_?name|given_?name|"
    r"email|e_?mail|phone|mobile|contact|address|addr|postcode|zip)",
    re.I,
)


def privacy_signal(attribute_name: str, data_type: str = "") -> str | None:
    """Return a coarse candidate category if the name looks sensitive, else None."""
    return "PII_CANDIDATE" if _PRIVACY.search(attribute_name or "") else None
