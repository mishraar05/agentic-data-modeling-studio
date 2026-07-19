"""Load merged Databricks job parameters from the ``metadata/`` folder.

Each task passes only ``env`` (e.g. dev/prod); this reads ``metadata/base.json``
overlaid with ``metadata/<env>.json`` and returns one flat dict. Values produced
mid-DAG (``source_tables``, snapshot ids, ``run_id``) are passed as task values
and override the file via ``resolve_job_params``. Secrets are never stored here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        if key == "_comment":
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_params(repo_root: str | Path, env: str = "dev",
                metadata_dir: str = "metadata") -> dict[str, Any]:
    """Return base.json merged with <env>.json (env wins). Comments stripped."""
    root = Path(repo_root)
    base = json.loads((root / metadata_dir / "base.json").read_text(encoding="utf-8"))
    base.pop("_comment", None)
    env_file = root / metadata_dir / f"{env}.json"
    if not env_file.exists():
        raise FileNotFoundError(f"No metadata file for env '{env}': {env_file}")
    override = json.loads(env_file.read_text(encoding="utf-8"))
    merged = _deep_merge(base, override)
    merged.pop("_comment", None)
    return merged


def resolve_job_params(dbutils, repo_root: str | Path, *,
                       dynamic_keys: tuple[str, ...] = ()) -> dict[str, Any]:  # pragma: no cover
    """Notebook entry point: read the ``env`` widget, load the merged params, then
    let any non-empty dynamic widgets (upstream task values) override the file."""
    env = (dbutils.widgets.get("env") or "dev").strip()
    params = load_params(repo_root, env)
    for key in dynamic_keys:
        try:
            value = dbutils.widgets.get(key).strip()
        except Exception:
            value = ""
        if value:
            params[key] = value
    return params
