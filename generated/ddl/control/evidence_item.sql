-- Auto-generated from evidence_item.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.evidence_item (
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
  provenance_class STRING NOT NULL,
  evidence_type STRING NOT NULL,
  content STRING NOT NULL,
  source_snapshot_ref STRING,
  profile_snapshot_ref STRING,
  document_set_ref STRING,
  document_locator STRING,
  source_object_name STRING,
  source_attribute_name STRING,
  governed_pack_id STRING,
  governed_pack_version STRING,
  fingerprint STRING NOT NULL,
  notes STRING,

  -- Constraints
  CONSTRAINT evidence_item_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.evidence_item ADD CONSTRAINT evidence_item_lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.evidence_item ADD CONSTRAINT evidence_item_provenance_class_check CHECK (provenance_class IN ('SOURCE_FACT', 'DOCUMENT_CLAIM', 'GOVERNED_INPUT', 'REQUIREMENT', 'INFERENCE', 'HUMAN_DECISION', 'UNRESOLVED'));
ALTER TABLE insurance_source_discovery.control.evidence_item ADD CONSTRAINT evidence_item_evidence_type_check CHECK (evidence_type IN ('METADATA', 'PROFILE', 'DOCUMENT_EXCERPT', 'REQUIREMENT', 'GLOSSARY_TERM', 'STANDARD', 'PRIOR_DECISION'));