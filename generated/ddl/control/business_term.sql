-- Auto-generated from business_term.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.business_term (
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
  evidence_item_ref STRING NOT NULL COMMENT 'Reference to supporting evidence',
  term STRING NOT NULL COMMENT 'The business term',
  definition STRING NOT NULL COMMENT 'Business definition of the term',
  synonyms ARRAY<STRING> COMMENT 'Alternative terms with same meaning',
  governed_equivalent STRING COMMENT 'Mapping to equivalent term in governed glossary',
  source_document_ref STRING COMMENT 'Reference to source document if from document_set',
  source_locator STRING COMMENT 'Page number or section identifier within document',
  review_decision_ref STRING COMMENT 'Reference to review decision (required when APPROVED)',

  -- Constraints
  CONSTRAINT business_term_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.business_term ADD CONSTRAINT business_term_lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED'));