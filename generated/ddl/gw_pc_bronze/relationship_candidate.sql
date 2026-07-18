-- Auto-generated from relationship_candidate.schema.json vunknown
-- Configuration: config/env_config.yaml (schema=gw_pc_bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.relationship_candidate (
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
  evidence_item_ref STRING NOT NULL COMMENT 'Reference to the parent evidence item',
  parent_object_observation_ref STRING NOT NULL COMMENT 'Reference to parent object observation',
  child_object_observation_ref STRING NOT NULL COMMENT 'Reference to child object observation',
  relationship_type STRING NOT NULL COMMENT 'Type of relationship',
  parent_attributes ARRAY<STRING> NOT NULL COMMENT 'Parent side attribute names',
  child_attributes ARRAY<STRING> NOT NULL COMMENT 'Child side attribute names',
  cardinality STRING NOT NULL COMMENT 'Relationship cardinality',
  profile_evidence_refs ARRAY<STRING> COMMENT 'References to supporting profile evidence',

  -- Constraints
  CONSTRAINT table_pk PRIMARY KEY (record_id),
  CONSTRAINT lifecycle_state_check CHECK (lifecycle_state IN ('COMMITTED', 'SUPERSEDED')),
  CONSTRAINT relationship_type_check CHECK (relationship_type IN ('PRIMARY_KEY', 'FOREIGN_KEY', 'INFERRED_FK', 'LOOKUP')),
  CONSTRAINT cardinality_check CHECK (cardinality IN ('1:1', '1:M', 'M:M'))
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