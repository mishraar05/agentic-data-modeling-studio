-- Auto-generated from engagement.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.engagement (
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
  client_name STRING NOT NULL,
  authorization_ref STRING NOT NULL,
  effective_start_date DATE NOT NULL,
  effective_end_date DATE,
  workspace_host STRING NOT NULL,
  source_access_granted BOOLEAN NOT NULL,
  profiling_policy STRING NOT NULL,
  output_catalog STRING NOT NULL,
  output_schema STRING NOT NULL,
  notes STRING,

  -- Constraints
  CONSTRAINT engagement_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.engagement ADD CONSTRAINT engagement_lifecycle_state_check CHECK (lifecycle_state IN ('ACTIVE', 'CLOSED', 'REJECTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.engagement ADD CONSTRAINT engagement_profiling_policy_check CHECK (profiling_policy IN ('FULL', 'METADATA_ONLY', 'RESTRICTED'));