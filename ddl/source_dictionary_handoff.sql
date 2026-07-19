-- Auto-generated from source_dictionary_handoff.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.source_dictionary_handoff (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  artifact_version_ref STRING NOT NULL COMMENT 'Reference to the artifact version being handed off',
  context_snapshot_ref STRING NOT NULL COMMENT 'Reference to the context snapshot',
  evidence_set_ref STRING NOT NULL COMMENT 'Reference to the evidence set',
  requirement_set_ref STRING NOT NULL COMMENT 'Reference to the requirement set',
  review_decision_ref STRING NOT NULL COMMENT 'Reference to approval decision',
  source_snapshot_ref STRING NOT NULL COMMENT 'Reference to the source snapshot',
  profile_snapshot_ref STRING COMMENT 'Optional reference to profile snapshot',
  artifact_dependency_refs ARRAY<STRING> COMMENT 'References to artifact dependency records',
  lineage_edge_refs ARRAY<STRING> COMMENT 'References to lineage edge records',
  open_question_refs ARRAY<STRING> COMMENT 'References to open questions',
  handoff_timestamp TIMESTAMP NOT NULL COMMENT 'ISO 8601 timestamp of handoff',
  object_count BIGINT NOT NULL COMMENT 'Number of SDD objects in handoff',
  attribute_count BIGINT NOT NULL COMMENT 'Number of SDD attributes in handoff',
  relationship_count BIGINT NOT NULL COMMENT 'Number of SDD relationships in handoff',
  code_value_count BIGINT NOT NULL COMMENT 'Number of SDD code values in handoff',
  coverage_percentage DOUBLE NOT NULL COMMENT 'Percentage of source attributes covered',
  open_question_count BIGINT NOT NULL COMMENT 'Number of open questions',
  handoff_fingerprint STRING NOT NULL COMMENT 'SHA-256 hash of handoff package',
  intended_consumer STRING NOT NULL COMMENT 'Intended downstream consumer',

  -- Constraints
  CONSTRAINT source_dictionary_handoff_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.source_dictionary_handoff ADD CONSTRAINT source_dictionary_handoff_lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'ISSUED', 'REVOKED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.source_dictionary_handoff ADD CONSTRAINT source_dictionary_handoff_intended_consumer_check CHECK (intended_consumer IN ('SILVER_MODELER', 'GOLD_MODELER'));