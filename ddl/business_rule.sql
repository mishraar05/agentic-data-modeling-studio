-- Auto-generated from business_rule.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=control)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.control.business_rule (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  solution_run_ref STRING NOT NULL COMMENT 'Reference to the solution run',
  evidence_item_ref STRING NOT NULL COMMENT 'Reference to supporting evidence',
  rule_text STRING NOT NULL COMMENT 'Full text of the business rule',
  rule_type STRING NOT NULL COMMENT 'Classification of business rule',
  affected_attributes ARRAY<STRING> COMMENT 'List of attribute names affected by this rule',
  source_document_ref STRING COMMENT 'Reference to source document if from document_set',
  source_locator STRING COMMENT 'Page number or section identifier within document',
  review_decision_ref STRING COMMENT 'Reference to review decision (required when APPROVED)',

  -- Constraints
  CONSTRAINT business_rule_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.control.business_rule ADD CONSTRAINT business_rule_lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.control.business_rule ADD CONSTRAINT business_rule_rule_type_check CHECK (rule_type IN ('VALIDATION', 'CALCULATION', 'TRANSFORMATION', 'DERIVATION'));