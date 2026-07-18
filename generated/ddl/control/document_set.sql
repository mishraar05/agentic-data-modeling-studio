-- Auto-generated from document_set.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.document_set (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  engagement_id STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<work_package_id: STRING, run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  work_package_ref STRING NOT NULL COMMENT 'Reference to the work package',
  document_count BIGINT NOT NULL COMMENT 'Number of documents in this set',
  document_locators ARRAY<STRING> NOT NULL COMMENT 'List of document locations',
  ingestion_timestamp TIMESTAMP NOT NULL COMMENT 'ISO 8601 timestamp when documents were ingested',
  fingerprint STRING NOT NULL COMMENT 'SHA-256 hash of document set for verification',

  -- Constraints
  CONSTRAINT document_set_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.document_set ADD CONSTRAINT document_set_lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'));