-- Auto-generated from lineage_edge.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.lineage_edge (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  solution_run_ref STRING NOT NULL COMMENT 'Reference to the solution run',
  source_type STRING NOT NULL COMMENT 'Type of source in lineage',
  source_ref STRING NOT NULL COMMENT 'Reference to the source record',
  target_ref STRING NOT NULL COMMENT 'Reference to the target record',
  transformation STRING COMMENT 'Description of transformation applied',
  evidence_item_ref STRING COMMENT 'Optional reference to supporting evidence',
  artifact_version_ref STRING COMMENT 'Optional reference to artifact version',

  -- Constraints
  CONSTRAINT lineage_edge_pk PRIMARY KEY (record_id)
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'governance.sensitivity_label' = 'INTERNAL',
  'governance.domain' = 'data_governance',
  'governance.purpose' = 'source_data_discovery'
)
;

-- CHECK constraints added via ALTER TABLE
ALTER TABLE insurance_source_discovery.control.lineage_edge ADD CONSTRAINT lineage_edge_lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.lineage_edge ADD CONSTRAINT lineage_edge_source_type_check CHECK (source_type IN ('SOURCE_ATTRIBUTE', 'EVIDENCE_ITEM', 'ARTIFACT'));