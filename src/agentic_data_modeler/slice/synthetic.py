"""REMOVED — hardcoded synthetic source tables are no longer part of the product.

Phase 1 now reads a real catalog via ``information_schema``
(``agentic_data_modeler.evidence.sql_catalog.DuckDBCatalogReader``), and the
source is bound from ``config/proof_slice.yaml`` (decisions D23-01 / D23-02).
Sample data for tests lives in ``tests/fixtures/`` as a swappable SQL fixture,
not in the runtime package.
"""

raise ImportError(
    "slice.synthetic has been removed. Read source metadata from a real catalog "
    "via evidence.sql_catalog + slice.source_binding.load_binding() instead."
)
