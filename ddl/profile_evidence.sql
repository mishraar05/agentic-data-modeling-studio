-- Auto-generated from profile_evidence.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.profile_evidence (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  profile_snapshot_ref STRING NOT NULL COMMENT 'Reference to the profile snapshot',
  evidence_item_ref STRING NOT NULL COMMENT 'Reference to the parent evidence item',
  object_name STRING NOT NULL COMMENT 'Parent table or view name',
  attribute_name STRING NOT NULL COMMENT 'Column name',
  row_count BIGINT NOT NULL COMMENT 'Total rows examined',
  null_count BIGINT NOT NULL COMMENT 'Number of NULL values',
  distinct_count BIGINT NOT NULL COMMENT 'Number of distinct values',
  min_value STRING COMMENT 'Minimum value observed',
  max_value STRING COMMENT 'Maximum value observed',
  top_values ARRAY<STRUCT<value: STRING, count: BIGINT>> COMMENT 'Most frequent values with counts',
  pattern_sample STRING COMMENT 'Representative pattern or format example',

  -- Constraints
  CONSTRAINT profile_evidence_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.profile_evidence ADD CONSTRAINT profile_evidence_lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'));