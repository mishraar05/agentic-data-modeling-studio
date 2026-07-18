-- Auto-generated from source_object_observation.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.source_object_observation (
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
  source_snapshot_ref STRING NOT NULL COMMENT 'Reference to the source snapshot',
  evidence_item_ref STRING NOT NULL COMMENT 'Reference to the parent evidence item',
  catalog_name STRING NOT NULL COMMENT 'Unity Catalog catalog name',
  schema_name STRING NOT NULL COMMENT 'Unity Catalog schema name',
  object_name STRING NOT NULL COMMENT 'Table or view name',
  object_type STRING NOT NULL COMMENT 'Type of database object',
  attribute_count BIGINT NOT NULL COMMENT 'Number of attributes in this object',
  constraint_observations ARRAY<STRUCT<constraint_type: STRING, constraint_details: STRING>> COMMENT 'List of constraints observed on this object',

  -- Constraints
  CONSTRAINT source_object_observation_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.source_object_observation ADD CONSTRAINT source_object_observation_lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.source_object_observation ADD CONSTRAINT source_object_observation_object_type_check CHECK (object_type IN ('TABLE', 'VIEW', 'MATERIALIZED_VIEW'));