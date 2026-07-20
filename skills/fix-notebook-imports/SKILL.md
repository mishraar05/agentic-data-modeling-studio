---
name: fix-notebook-imports
description: >-
  Build spec for Genie Code to fix the missing-import and syntax errors in the
  src/workflows notebooks found by static analysis (pyflakes + py_compile): a fatal
  f-string syntax error in profile_source, and undefined-name crashes in
  snapshot_source_metadata, assemble_source_evidence, and analyze_source_dictionary that
  only surface mid-run. Use when notebooks fail with NameError (e.g. name 'F'/'datetime'/
  'MetadataInventory' is not defined) or SyntaxError. HARD RULE: only add the missing
  imports / fix the syntax — do not reorder, refactor, or change any logic, and never
  touch analyst/*, contracts, the loader, metadata, or passing tests.
---

# Fix workflow-notebook imports + one syntax error

## Status and authority

Version: `0.1.0-DRAFT` · Owner: solution/platform owner (`TBD`)
These notebooks compile at the top but **use symbols they never import**, so they crash
only when execution reaches that line (which is why fixing one task keeps uncovering the
next failure). Root cause: the metadata-param refactor rewrote each notebook's header/param
cell and dropped adjacent import lines. This skill restores the missing imports and fixes
one fatal syntax error. It is **purely additive to import blocks** — no logic changes.

Verified by `python -m pyflakes src/workflows/*.py` and `python -m py_compile` (filtering
the Databricks-injected globals `spark`, `dbutils`, `display`, `sc`).

---

## 0. PROTECTED — do not modify

- `src/agentic_data_modeler/**` (analyst, evidence, config loader, contracts logic),
  `contracts/**`, `generated/ddl/**`, `metadata/*.json`, and any passing test.
- The notebooks' **logic, cell order, and `# COMMAND ----------` structure** — touch only
  the import lines (and the one malformed f-string in Fix 1). Do not "tidy" or reorder code.

Golden rule: add the exact missing imports and nothing else. Every symbol added below is
already exported by the target module (verified against `agentic_data_modeler/evidence/__init__.py`);
do not create new modules or change what those modules export.

---

## 1. FATAL — fix the `profile_source.py` syntax error first

`src/workflows/profile_source.py` does not compile (`py_compile` fails). Line ~283:
```python
notes = f"{"" }; policy_ref={policy_ref}; retention_until={retention_until}"
```
The nested quotes in the f-string are invalid. Read the surrounding lines to preserve
intent, then replace with a valid f-string that keeps the `policy_ref`/`retention_until`
placeholders and drops the broken `{"" }` segment, e.g.:
```python
notes = f"policy_ref={policy_ref}; retention_until={retention_until}"
```
Then add its missing imports (see Fix 2). After this, re-run
`python -m pyflakes src/workflows/profile_source.py` to enumerate any remaining undefined
names the syntax error was hiding (expected: `F`, `defaultdict`, `datetime`, `timezone`,
`timedelta`, `hashlib`, `AttributeProfile`, `ProfileInventory`; also confirm `DQProfiler`
and `WorkspaceClient` are imported — add them from their existing modules if missing).

## 2. Add the missing imports (exact, per file)

Add these to each file's top-level import block. Do not remove existing imports.

**`src/workflows/snapshot_source_metadata.py`** (already has `F`):
```python
import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from agentic_data_modeler.evidence import (
    ColumnMetadata, ConstraintMetadata, MetadataInventory, ObjectMetadata,
    one_based_ordinal_offset, stable_record_id,
)
```

**`src/workflows/assemble_source_evidence.py`**:
```python
from datetime import datetime, timezone
from pyspark.sql import functions as F
from agentic_data_modeler.evidence import EvidenceItemReference, EvidenceSetManifest
```

**`src/workflows/profile_source.py`** (in addition to Fix 1):
```python
import hashlib
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pyspark.sql import functions as F
from agentic_data_modeler.evidence import AttributeProfile, ProfileInventory
```
Keep whatever `DQProfiler` / `WorkspaceClient` imports already exist; add them only if
pyflakes still reports them undefined after Fix 1.

**`src/workflows/analyze_source_dictionary.py`** — it imports only `PurePosixPath` but uses
`Path`. Change:
```python
from pathlib import PurePosixPath
```
to:
```python
from pathlib import Path, PurePosixPath
```

## 3. Minor cleanups (optional, safe)

- Remove the unused `import os` in the notebooks pyflakes flags (`discover_source_scope`,
  `assemble_context`, `analyze_source_relationships`, `register_solution_run`,
  `validate_source_discovery_scope`, `snapshot_source_metadata`) — only if `os` is truly
  unused there (grep `\bos\.` in the file first; the REPO_ROOT helper now uses `sys.path`, not `os`).
- `export_source_dictionary.py`: the f-string with no placeholders (~line 83) and the unused
  `except ... as e` (~line 98) are cosmetic — fix only if trivial.

## 4. Orphan file check — the duplicate validate notebook

There are two validate notebooks: `00_validate_scope.py` and `validate_source_discovery_scope.py`.
The job (`resources/*.job.yml`) calls only `validate_source_discovery_scope.py`. Confirm
`00_validate_scope.py` is unreferenced:
```
grep -rn "00_validate_scope" resources src scripts
```
If nothing references it, delete `00_validate_scope.py`. If anything does, **STOP and ask** —
do not delete a referenced file.

## 5. Mandatory validations (all must pass)

- `python -m py_compile src/workflows/*.py` — every file compiles (profile_source included).
- `python -m pyflakes src/workflows/*.py` — no `undefined name` results other than the
  Databricks-injected globals `spark`, `dbutils`, `display`, `sc` (filter those out).
- `pytest -q` — baseline unchanged (these are notebooks, not imported by the unit suite, but
  confirm nothing regressed).
- `git diff` shows only added/edited import lines, the one f-string fix, and (optionally) the
  removed unused `os` lines / deleted orphan — **no logic changes**.

## 6. Stop / escalation

- After Fix 1, if pyflakes reports an undefined name whose source module is unclear (e.g.
  `DQProfiler`, `WorkspaceClient`) -> find its real import path; if you cannot, STOP and ask.
- If adding an import would require changing what a PROTECTED module exports -> STOP; the
  symbol should already exist there (verify the name/spelling), do not add exports.
- `00_validate_scope.py` is referenced somewhere -> STOP, ask before deleting.
- Any fix seems to need a logic change -> STOP; this skill is imports/syntax only.

## Acceptance

Every `src/workflows/*.py` compiles and is pyflakes-clean (bar injected globals); the four
broken notebooks (`profile_source`, `snapshot_source_metadata`, `assemble_source_evidence`,
`analyze_source_dictionary`) no longer have undefined names; only imports/one f-string
changed; and the orphan validate notebook is resolved.
