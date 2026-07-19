"""Load merged Databricks job parameters from the ``metadata/`` folder.

Each task passes only dynamic runtime values (run_id, source_tables, snapshot ids,
work_package_id); this reads ``metadata/common.json`` overlaid with
``metadata/sdd_param.json`` and returns one nested dict. Secrets are never stored here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursive dict merge. Override wins at every level. Ignores _comment."""
    out = dict(base)
    for key, value in override.items():
        if key == "_comment":
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_params(repo_root: str | Path, metadata_dir: str = "metadata") -> dict[str, Any]:
    """Return common.json merged with sdd_param.json (override wins). Comments stripped.
    
    Raises:
        FileNotFoundError: If either common.json or sdd_param.json is missing.
    """
    root = Path(repo_root)
    common_file = root / metadata_dir / "common.json"
    if not common_file.exists():
        raise FileNotFoundError(f"Missing metadata file: {common_file}")
    
    common = json.loads(common_file.read_text(encoding="utf-8"))
    common.pop("_comment", None)
    
    override_file = root / metadata_dir / "sdd_param.json"
    if not override_file.exists():
        raise FileNotFoundError(f"Missing metadata file: {override_file}")
    
    override = json.loads(override_file.read_text(encoding="utf-8"))
    merged = _deep_merge(common, override)
    merged.pop("_comment", None)
    return merged


def resolve_job_params(
    dbutils, 
    repo_root: str | Path, 
    *, 
    dynamic_keys: tuple[str, ...] = ()
) -> dict[str, Any]:  # pragma: no cover
    """Notebook entry point: load the merged params, then let any non-empty dynamic
    widgets (upstream task values) override the file.
    
    Args:
        dbutils: Databricks utilities object
        repo_root: Root directory of the repository
        dynamic_keys: Tuple of widget keys to read and override if non-empty
        
    Returns:
        Nested dict with merged parameters
    """
    params = load_params(repo_root)
    for key in dynamic_keys:
        try:
            value = dbutils.widgets.get(key).strip()
        except Exception:
            value = ""
        if value:
            params[key] = value
    return params