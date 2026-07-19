-- Auto-generated from evidence_set.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.evidence_set (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  solution_run_ref STRING NOT NULL COMMENT 'Reference to the solution run that assembled this evidence',
  source_snapshot_ref STRING NOT NULL COMMENT 'Reference to the source snapshot',
  profile_snapshot_ref STRING COMMENT 'Reference to the profile snapshot if profiling was performed',
  document_set_ref STRING COMMENT 'Reference to the document set if documents were provided',
  requirement_set_ref STRING COMMENT 'Reference to the requirement set if requirements were extracted',
  evidence_item_count BIGINT NOT NULL COMMENT 'Number of evidence items in this set',
  assembly_timestamp TIMESTAMP NOT NULL COMMENT 'ISO 8601 timestamp when evidence was assembled',
  fingerprint STRING NOT NULL COMMENT 'SHA-256 hash of evidence set for verification',

  -- Constraints
  CONSTRAINT evidence_set_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.evidence_set ADD CONSTRAINT evidence_set_lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'));