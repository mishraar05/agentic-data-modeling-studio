-- Auto-generated from review_item.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.review_item (
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
  artifact_version_ref STRING NOT NULL COMMENT 'Reference to the artifact version under review',
  validation_finding_refs ARRAY<STRING> COMMENT 'References to related validation findings',
  review_question STRING NOT NULL COMMENT 'The question requiring review',
  assigned_to STRING COMMENT 'Email or identifier of assigned reviewer',
  resolution_timestamp TIMESTAMP COMMENT 'ISO 8601 timestamp when item was resolved',

  -- Constraints
  CONSTRAINT review_item_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.review_item ADD CONSTRAINT review_item_lifecycle_state_check CHECK (lifecycle_state IN ('OPEN', 'RESOLVED', 'SUPERSEDED'));