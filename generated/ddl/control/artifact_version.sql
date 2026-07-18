-- Auto-generated from artifact_version.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.artifact_version (
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
  solution_run_ref STRING NOT NULL COMMENT 'Reference to the solution run that produced this version',
  artifact_type STRING NOT NULL COMMENT 'Type of artifact being versioned',
  artifact_count BIGINT NOT NULL COMMENT 'Number of records in this artifact version',
  version_number STRING NOT NULL COMMENT 'Semantic version number (major.minor.patch)',
  supersedes_version STRING COMMENT 'Previous version that this replaces, if any',
  review_decision_ref STRING COMMENT 'Reference to review decision record (required when lifecycle_state is APPROVED)',

  -- Constraints
  CONSTRAINT artifact_version_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.artifact_version ADD CONSTRAINT artifact_version_lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.artifact_version ADD CONSTRAINT artifact_version_artifact_type_check CHECK (artifact_type IN ('SDD_OBJECT', 'SDD_ATTRIBUTE', 'SDD_RELATIONSHIP', 'SDD_CODE_VALUE', 'SDD_HANDOFF'));