"""Job-parameter loader: base + env override merge."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentic_data_modeler.job_params import _deep_merge, load_params


def test_deep_merge_overrides_and_keeps_base():
    merged = _deep_merge({"a": 1, "b": {"x": 1, "y": 2}}, {"b": {"y": 9}, "c": 3})
    assert merged == {"a": 1, "b": {"x": 1, "y": 9}, "c": 3}


def test_load_dev_merges_base_and_env():
    p = load_params(ROOT, "dev")
    # base values survive
    assert p["source_catalog"] == "insurance_source_discovery"
    assert p["source_scope_mode"] == "SCHEMA_ALL_TABLES"
    assert p["pack_id"] == "public_us_pnc_personal_auto"
    # env-only values present
    assert "producer_endpoint" in p and "critic_endpoint" in p
    assert p["source_access_granted"] == "true"
    # comments never leak into params
    assert "_comment" not in p


def test_unknown_env_fails_closed():
    import pytest
    with pytest.raises(FileNotFoundError):
        load_params(ROOT, "nope")
