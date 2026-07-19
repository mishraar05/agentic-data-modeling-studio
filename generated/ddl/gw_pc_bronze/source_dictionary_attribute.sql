-- Auto-generated from source_dictionary_attribute.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.source_dictionary_attribute (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  context_snapshot_ref STRING NOT NULL,
  source_attribute_observation_ref STRING NOT NULL,
  source_object_name STRING NOT NULL,
  source_attribute_name STRING NOT NULL,
  ordinal_position BIGINT NOT NULL,
  physical_type STRUCT<value: STRING, value_type: STRING, evidence_refs: ARRAY<STRING>> NOT NULL,
  physical_length STRUCT<value: STRING, value_type: STRING, evidence_refs: ARRAY<STRING>>,
  physical_precision STRUCT<value: STRING, value_type: STRING, evidence_refs: ARRAY<STRING>>,
  physical_scale STRUCT<value: STRING, value_type: STRING, evidence_refs: ARRAY<STRING>>,
  physical_nullable STRUCT<value: STRING, value_type: STRING, evidence_refs: ARRAY<STRING>> NOT NULL,
  business_name STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  business_definition STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  business_purpose STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>>,
  synonyms STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>>,
  subject_area STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>>,
  key_role STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>>,
  privacy_class STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>>,
  retention_rule STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>>,
  code_set_ref STRING,
  profile_evidence_refs ARRAY<STRING>,
  relationship_refs ARRAY<STRING>,
  open_question_refs ARRAY<STRING>,
  review_decision_ref STRING,
  notes STRING,

  -- Constraints
  CONSTRAINT source_dictionary_attribute_pk PRIMARY KEY (record_id)
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

-- CHECK constraints added via ALTER TABLE
ALTER TABLE insurance_source_discovery.gw_pc_bronze.source_dictionary_attribute ADD CONSTRAINT source_dictionary_attribute_lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED'));