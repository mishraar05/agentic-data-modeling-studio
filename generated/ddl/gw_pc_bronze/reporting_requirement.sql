-- Auto-generated from reporting_requirement.schema.json vunknown
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.reporting_requirement (
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
  requirement_text STRING NOT NULL COMMENT 'Full text of the requirement',
  acceptance_criteria STRING NOT NULL COMMENT 'Criteria for requirement satisfaction',
  priority STRING NOT NULL COMMENT 'Requirement priority',
  report_name STRING COMMENT 'Name of the report or dashboard',
  metric_name STRING COMMENT 'Name of the specific metric',
  calculation_logic STRING COMMENT 'Business logic for metric calculation',
  source_document_ref STRING COMMENT 'Reference to source document if from document_set',
  source_locator STRING COMMENT 'Page number or section identifier within document',
  review_decision_ref STRING COMMENT 'Reference to review decision (required when APPROVED)',

  -- Constraints
  CONSTRAINT table_pk PRIMARY KEY (record_id),
  CONSTRAINT lifecycle_state_check CHECK (lifecycle_state IN ('DRAFT', 'APPROVED', 'REJECTED', 'SUPERSEDED')),
  CONSTRAINT priority_check CHECK (priority IN ('MUST', 'SHOULD', 'NICE_TO_HAVE'))
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