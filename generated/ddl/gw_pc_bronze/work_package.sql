-- Auto-generated from work_package.schema.json vunknown
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.work_package (
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
  engagement_ref STRING NOT NULL,
  workflow_state STRING NOT NULL,
  source_catalog STRING NOT NULL,
  source_schema STRING NOT NULL,
  source_tables_allow_list ARRAY<STRING> NOT NULL,
  source_product STRING,
  source_module STRING,
  source_version STRING,
  knowledge_pack_id STRING,
  knowledge_pack_version STRING,
  output_catalog STRING NOT NULL,
  output_schema STRING NOT NULL,
  authorization_validated_at TIMESTAMP,
  notes STRING,

  -- Constraints
  CONSTRAINT table_pk PRIMARY KEY (record_id),
  CONSTRAINT lifecycle_state_check CHECK (lifecycle_state IN ('ACTIVE', 'CLOSED', 'REJECTED', 'SUPERSEDED')),
  CONSTRAINT workflow_state_check CHECK (workflow_state IN ('VALIDATED', 'METADATA_READY', 'PROFILE_READY', 'EVIDENCE_READY', 'CONTEXT_READY', 'SDD_READY', 'SILVER_READY', 'GOLD_READY', 'STTM_READY', 'PUBLISHED'))
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