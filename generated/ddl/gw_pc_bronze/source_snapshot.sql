-- Auto-generated from source_snapshot.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.source_snapshot (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  solution_run_ref STRING NOT NULL,
  snapshot_timestamp TIMESTAMP NOT NULL,
  source_catalog STRING NOT NULL,
  source_schema STRING NOT NULL,
  captured_table_count BIGINT NOT NULL,
  captured_column_count BIGINT NOT NULL,
  metadata_query_ref STRING NOT NULL,
  fingerprint STRING NOT NULL,
  notes STRING,

  -- Constraints
  CONSTRAINT source_snapshot_pk PRIMARY KEY (record_id)
)
USING DELTA
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'governance.sensitivity_label' = 'INTERNAL',
  'governance.domain' = 'data_governance',
  'governance.product_line' = 'guidewire_pc',
  'governance.layer' = 'bronze',
  'governance.purpose' = 'source_data_discovery'
)
;

-- CHECK constraints added via ALTER TABLE
ALTER TABLE insurance_source_discovery.gw_pc_bronze.source_snapshot ADD CONSTRAINT source_snapshot_lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'));