-- Auto-generated from source_dictionary_object.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.source_dictionary_object (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  context_snapshot_ref STRING NOT NULL COMMENT 'Reference to the context snapshot (required for contextual provenance)',
  source_object_observation_ref STRING NOT NULL COMMENT 'Reference to the source object observation',
  evidence_item_ref STRING NOT NULL COMMENT 'Reference to supporting evidence',
  source_object_name STRING NOT NULL COMMENT 'Fully qualified source object name',
  business_name STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  business_definition STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  business_purpose STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  entity_type STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  attribute_refs ARRAY<STRING> NOT NULL COMMENT 'References to attribute records',
  relationship_refs ARRAY<STRING> COMMENT 'References to relationship records',
  review_decision_ref STRING COMMENT 'Reference to review decision (required when APPROVED)',
  open_question_refs ARRAY<STRING> COMMENT 'References to open questions',

  -- Constraints
  CONSTRAINT source_dictionary_object_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.source_dictionary_object ADD CONSTRAINT source_dictionary_object_lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED'));