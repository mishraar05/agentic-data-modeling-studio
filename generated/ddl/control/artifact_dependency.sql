-- Auto-generated from artifact_dependency.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.artifact_dependency (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  artifact_version_ref STRING NOT NULL COMMENT 'Reference to the artifact version',
  depends_on_context_snapshot_ref STRING COMMENT 'Reference to context snapshot dependency',
  depends_on_evidence_set_ref STRING COMMENT 'Reference to evidence set dependency',
  depends_on_requirement_set_ref STRING COMMENT 'Reference to requirement set dependency',
  dependency_type STRING NOT NULL COMMENT 'Type of dependency relationship',

  -- Constraints
  CONSTRAINT artifact_dependency_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.artifact_dependency ADD CONSTRAINT artifact_dependency_lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.artifact_dependency ADD CONSTRAINT artifact_dependency_dependency_type_check CHECK (dependency_type IN ('GOVERNED_CONTEXT', 'SOURCE_EVIDENCE', 'REQUIREMENT', 'PRIOR_VERSION'));