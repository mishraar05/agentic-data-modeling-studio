"""DEPRECATED: This module has been moved to agentic_data_modeler.config.job_params

This file is kept temporarily for backwards compatibility during the refactoring.
All imports should now use:
    from agentic_data_modeler.config.job_params import load_params, resolve_job_params

This file will be removed once all notebooks and workflows are updated.
"""

import warnings
from agentic_data_modeler.config.job_params import (
    load_params as _load_params,
    resolve_job_params as _resolve_job_params,
    _deep_merge as __deep_merge,
)

warnings.warn(
    "agentic_data_modeler.job_params is deprecated. "
    "Use agentic_data_modeler.config.job_params instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export for backwards compatibility
load_params = _load_params
resolve_job_params = _resolve_job_params
_deep_merge = __deep_merge
