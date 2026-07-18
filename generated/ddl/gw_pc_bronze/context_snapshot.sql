-- Auto-generated from context_snapshot.schema.json vunknown
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.context_snapshot (
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
  work_package_ref STRING NOT NULL,
  evidence_set_ref STRING NOT NULL,
  requirement_set_ref STRING,
  snapshot_timestamp TIMESTAMP NOT NULL,
  knowledge_pack_id STRING NOT NULL,
  knowledge_pack_version STRING NOT NULL,
  selected_modules ARRAY<STRING> NOT NULL,
  context_effective_date DATE NOT NULL,
  glossary_term_count BIGINT,
  code_set_count BIGINT,
  kpi_count BIGINT,
  context_size_bytes BIGINT NOT NULL,
  context_fingerprint STRING NOT NULL,
  budget_compliance BOOLEAN NOT NULL,
  notes STRING,

  -- Constraints
  CONSTRAINT table_pk PRIMARY KEY (record_id),
  CONSTRAINT lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'))
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