-- Auto-generated from source_dictionary_code_value.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.source_dictionary_code_value (
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
  context_snapshot_ref STRING NOT NULL COMMENT 'Reference to the context snapshot (required for contextual provenance)',
  attribute_ref STRING NOT NULL COMMENT 'Reference to the parent source_dictionary_attribute',
  evidence_item_ref STRING NOT NULL COMMENT 'Reference to supporting evidence',
  code STRING NOT NULL COMMENT 'The code value',
  meaning STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  frequency BIGINT COMMENT 'Occurrence count from profile evidence',
  governed_code_ref STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>,
  profile_evidence_ref STRING COMMENT 'Reference to profile evidence supporting this code value',
  review_decision_ref STRING COMMENT 'Reference to review decision (required when APPROVED)',
  open_question_refs ARRAY<STRING> COMMENT 'References to open questions',

  -- Constraints
  CONSTRAINT source_dictionary_code_value_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.source_dictionary_code_value ADD CONSTRAINT source_dictionary_code_value_lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED'));