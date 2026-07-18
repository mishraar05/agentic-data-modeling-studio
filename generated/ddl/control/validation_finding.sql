-- Auto-generated from validation_finding.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.validation_finding (
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
  artifact_version_ref STRING NOT NULL COMMENT 'Reference to the artifact version being validated',
  finding_type STRING NOT NULL COMMENT 'Category of validation finding',
  severity STRING NOT NULL COMMENT 'Severity level of the finding',
  finding_text STRING NOT NULL COMMENT 'Description of the validation finding',
  affected_record_refs ARRAY<STRING> COMMENT 'References to records affected by this finding',
  evidence_item_ref STRING COMMENT 'Optional reference to supporting evidence',

  -- Constraints
  CONSTRAINT validation_finding_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.validation_finding ADD CONSTRAINT validation_finding_lifecycle_state_check CHECK (lifecycle_state IN ('OPEN', 'RESOLVED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.validation_finding ADD CONSTRAINT validation_finding_finding_type_check CHECK (finding_type IN ('SCHEMA', 'REFERENTIAL', 'COVERAGE', 'POLICY', 'CONTRADICTION'));
ALTER TABLE insurance_source_discovery.control.validation_finding ADD CONSTRAINT validation_finding_severity_check CHECK (severity IN ('BLOCKING', 'ERROR', 'WARNING', 'INFO'));