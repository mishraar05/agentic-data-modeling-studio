-- Auto-generated from relationship_candidate.schema.json v0.2.0
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.relationship_candidate (
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
  source_snapshot_ref STRING NOT NULL,
  evidence_set_ref STRING NOT NULL,
  parent_object_observation_ref STRING NOT NULL,
  child_object_observation_ref STRING NOT NULL,
  parent_object_name STRING NOT NULL,
  child_object_name STRING NOT NULL,
  parent_attributes ARRAY<STRING> NOT NULL,
  child_attributes ARRAY<STRING> NOT NULL,
  relationship_type STRING NOT NULL,
  relationship_name STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  cardinality STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  optionality STRUCT<value: STRING, value_type: STRING, governed_code_ref: STRUCT<pack_id: STRING, pack_version: STRING, code_set_id: STRING, fingerprint: STRING, code: STRING>, evidence_state: STRING, evidence_refs: ARRAY<STRING>, review_decision_ref: STRING, open_question_ref: STRING, confidence: STRUCT<evidence_type: STRING, evidence_count: BIGINT, critic_agreement: STRING>, assumptions: ARRAY<STRING>, contradictions: ARRAY<STRING>> NOT NULL,
  rationale STRING NOT NULL,
  evidence_refs ARRAY<STRING> NOT NULL,
  memory_refs ARRAY<STRING>,
  critic_status STRING NOT NULL,
  review_decision_ref STRING,
  open_question_refs ARRAY<STRING>,

  -- Constraints
  CONSTRAINT relationship_candidate_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.gw_pc_bronze.relationship_candidate ADD CONSTRAINT relationship_candidate_lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.gw_pc_bronze.relationship_candidate ADD CONSTRAINT relationship_candidate_relationship_type_check CHECK (relationship_type IN ('FOREIGN_KEY', 'INFERRED_FK', 'LOOKUP', 'BRIDGE', 'SELF_REFERENCE'));
ALTER TABLE insurance_source_discovery.gw_pc_bronze.relationship_candidate ADD CONSTRAINT relationship_candidate_critic_status_check CHECK (critic_status IN ('CONFIRMED', 'CONTESTED', 'NOT_ASSESSED'));