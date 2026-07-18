-- Auto-generated from open_question.schema.json vunknown
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.open_question (
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
  work_package_ref STRING NOT NULL COMMENT 'Reference to the work package',
  question_text STRING NOT NULL COMMENT 'The open question',
  question_type STRING NOT NULL COMMENT 'Category of open question',
  affected_artifacts ARRAY<STRING> COMMENT 'References to affected artifact records',
  context_snapshot_ref STRING COMMENT 'Optional reference to context snapshot',
  evidence_item_ref STRING COMMENT 'Optional reference to related evidence',
  resolution_answer STRING COMMENT 'Answer or resolution (required when RESOLVED)',

  -- Constraints
  CONSTRAINT table_pk PRIMARY KEY (record_id),
  CONSTRAINT lifecycle_state_check CHECK (lifecycle_state IN ('OPEN', 'RESOLVED', 'SUPERSEDED')),
  CONSTRAINT question_type_check CHECK (question_type IN ('MISSING_EVIDENCE', 'AMBIGUOUS_MEANING', 'CONFLICTING_EVIDENCE', 'UNCLEAR_REQUIREMENT'))
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