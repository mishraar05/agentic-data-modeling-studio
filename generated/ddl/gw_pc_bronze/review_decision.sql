-- Auto-generated from review_decision.schema.json v0.1.0
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.review_decision (
  record_id STRING NOT NULL,
  schema_version STRING NOT NULL,
  lob STRING NOT NULL,
  domain STRING NOT NULL,
  artifact_version STRING NOT NULL,
  lifecycle_state STRING NOT NULL,
  provenance STRUCT<run_id: STRING, context_snapshot_id: STRING, source_snapshot_id: STRING, profile_snapshot_id: STRING, model_version: STRING, prompt_version: STRING, skill_version: STRING, tool_version: STRING> NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL,
  review_item_ref STRING NOT NULL COMMENT 'Reference to the review item',
  decision STRING NOT NULL COMMENT 'The decision made',
  decision_maker STRING NOT NULL COMMENT 'Email or identifier of decision maker',
  decision_timestamp TIMESTAMP NOT NULL COMMENT 'ISO 8601 timestamp of decision',
  rationale STRING NOT NULL COMMENT 'Explanation for the decision',
  impact_scope ARRAY<STRING> COMMENT 'References to artifacts affected by this decision',
  evidence_item_ref STRING COMMENT 'Optional reference to additional evidence',

  -- Constraints
  CONSTRAINT review_decision_pk PRIMARY KEY (record_id)
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
ALTER TABLE insurance_source_discovery.gw_pc_bronze.review_decision ADD CONSTRAINT review_decision_lifecycle_state_check CHECK (lifecycle_state IN ('RECORDED', 'SUPERSEDED'));
ALTER TABLE insurance_source_discovery.gw_pc_bronze.review_decision ADD CONSTRAINT review_decision_decision_check CHECK (decision IN ('APPROVE', 'REJECT', 'REVISE', 'DEFER'));