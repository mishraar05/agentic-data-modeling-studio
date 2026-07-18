-- Auto-generated from source_attribute_observation.schema.json vunknown
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.source_attribute_observation (
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
  object_name STRING NOT NULL COMMENT 'Parent table or view name',
  attribute_name STRING NOT NULL COMMENT 'Column name',
  ordinal_position BIGINT NOT NULL COMMENT 'Column position (1-based)',
  data_type STRING NOT NULL COMMENT 'SQL data type from source metadata',
  nullable BOOLEAN NOT NULL COMMENT 'Whether NULL values are permitted',
  default_value STRING COMMENT 'Default value expression if any',
  length BIGINT COMMENT 'Length for character types',
  precision BIGINT COMMENT 'Precision for numeric types',
  scale BIGINT COMMENT 'Scale for numeric types',
  constraint_role STRING NOT NULL COMMENT 'Constraint role this attribute participates in',

  -- Constraints
  CONSTRAINT table_pk PRIMARY KEY (record_id),
  CONSTRAINT lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED')),
  CONSTRAINT constraint_role_check CHECK (constraint_role IN ('PRIMARY_KEY', 'FOREIGN_KEY', 'UNIQUE', 'CHECK', 'NONE'))
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