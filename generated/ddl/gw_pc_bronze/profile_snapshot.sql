-- Auto-generated from profile_snapshot.schema.json vunknown
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.profile_snapshot (
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
  source_snapshot_ref STRING NOT NULL COMMENT 'Reference to the source snapshot that was profiled',
  profiling_mode STRING NOT NULL COMMENT 'Extent of profiling performed',
  profile_timestamp TIMESTAMP NOT NULL COMMENT 'ISO 8601 timestamp of profile execution',
  profiled_table_count BIGINT NOT NULL COMMENT 'Number of tables profiled',
  profiled_attribute_count BIGINT NOT NULL COMMENT 'Total number of attributes profiled',
  profile_query_ref STRING NOT NULL COMMENT 'Reference to query execution that generated this profile',
  fingerprint STRING NOT NULL COMMENT 'SHA-256 hash of profiling results for verification',

  -- Constraints
  CONSTRAINT table_pk PRIMARY KEY (record_id),
  CONSTRAINT lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED')),
  CONSTRAINT profiling_mode_check CHECK (profiling_mode IN ('FULL', 'METADATA_ONLY', 'RESTRICTED'))
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