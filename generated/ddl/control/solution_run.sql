-- Auto-generated from solution_run.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.solution_run (
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
  work_package_ref STRING NOT NULL COMMENT 'Reference to the work package record ID',
  run_type STRING NOT NULL COMMENT 'Type of solution execution',
  start_timestamp TIMESTAMP NOT NULL COMMENT 'ISO 8601 timestamp when the run started',
  end_timestamp TIMESTAMP NOT NULL COMMENT 'ISO 8601 timestamp when the run completed or failed',
  status STRING NOT NULL COMMENT 'Current execution status',
  error_message STRING COMMENT 'Error details if status is FAILED',
  cost_usd DOUBLE COMMENT 'Approximate compute cost in USD for this run',

  -- Constraints
  CONSTRAINT solution_run_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.solution_run ADD CONSTRAINT solution_run_lifecycle_state_check CHECK (lifecycle_state IN ('ACTIVE', 'CLOSED', 'REJECTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.solution_run ADD CONSTRAINT solution_run_run_type_check CHECK (run_type IN ('VALIDATE', 'METADATA', 'PROFILE', 'EVIDENCE', 'CONTEXT', 'SDD', 'REVIEW'));
ALTER TABLE insurance_source_discovery.control.solution_run ADD CONSTRAINT solution_run_status_check CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'));