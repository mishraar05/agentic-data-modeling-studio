"""Job-parameter loader: common.json + sdd_param.json override merge."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agentic_data_modeler.config.job_params import _deep_merge, load_params


def test_deep_merge_overrides_and_keeps_base():
    merged = _deep_merge({"a": 1, "b": {"x": 1, "y": 2}}, {"b": {"y": 9}, "c": 3})
    assert merged == {"a": 1, "b": {"x": 1, "y": 9}, "c": 3}


def test_load_params_merges_common_and_sdd():
    p = load_params(ROOT)
    # common.json values survive (grouped structure)
    assert p["source"]["catalog"] == "insurance_source_discovery"
    assert p["scope"]["source_scope_mode"] == "SCHEMA_ALL_TABLES"
    assert p["knowledge_pack"]["pack_id"] == "public_us_pnc_personal_auto"
    # sdd_param.json override values present
    assert "producer_endpoint" in p["models"] and "critic_endpoint" in p["models"]
    assert p["identity"]["source_access_granted"] == "true"
    # comments never leak into params
    assert "_comment" not in p


def test_missing_file_fails_closed():
    import pytest
    import tempfile
    # Test with a directory that has no metadata files
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            load_params(tmpdir)
