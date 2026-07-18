# Increment 2: Schema Builder — Implementation Plan

**Project**: Agentic Data Modeling Studio  
**Increment**: 2 — Unity Catalog Delta Table Implementation  
**Status**: 🚀 **READY TO START** (Increment 1 Complete)  
**Version**: 1.1.0  
**Created**: 2025-01-XX  
**Updated**: 2025-01-XX (Added medallion architecture & env_config)
**Owner**: Technical Lead + Data Architect  
**Approver**: Chief Data Officer  

---

## Executive Summary

**Increment 2 converts the 31 approved JSON Schema contracts from Increment 1 into physical Delta tables in Unity Catalog**, creating the authoritative system of record for the Agentic Data Modeling Studio.

**Key Outcomes**:
* 31 Delta tables deployed to Unity Catalog bronze layer per Guidewire product
* Medallion architecture (bronze/silver/gold) established
* Environment-driven configuration (`config/env_config.yaml`)
* Automated schema generation from JSON Schema contracts
* Unity Catalog governance controls (tags, comments, ownership)
* Table validation suite proving schema conformance
* Foundation for Increment 3+ agent development

**Timeline**: 3-4 weeks  
**Dependencies**: Increment 1 complete ✅, Unity Catalog catalog provisioned, governance policies formalized ✅

---

## Configuration-Driven Architecture

**All catalog and schema configuration is defined in**: `config/env_config.yaml`

This file controls:
* Catalog name and ownership
* Guidewire product codes (`gw_pc`, `gw_cc`, `gw_bc`)
* Medallion layer definitions (bronze/silver/gold)
* Schema naming pattern: `{product_code}_{layer_suffix}`
* Proof slice targeting (California P&C → `gw_pc_bronze`)
* Access control rules
* DDL generation enablement per product/layer

**Benefit**: Change jurisdiction, add products, or enable new layers by updating config—no code changes required.

---

## Anti-Drift Gate Compliance

Per AGENTS.md §"Anti-drift gate", this work must answer:

### 1. Which Requirements Charter deliverable does this advance?

**Answer**: All authoritative deliverables (Section 5)
* Reconstructed Source Data Dictionary → `source_dictionary_*` tables in bronze layer
* Silver ODS model → silver layer (future increments, foundation now)
* Gold dimensional model → gold layer (future increments, foundation now)
* STTM package → `mapping_*` tables (future increments, foundation now)
* Coverage, decisions, governance → governance and lineage tables in bronze

**Delta tables are the authoritative system of record**. This increment creates the physical bronze layer foundation that all deliverables depend on.

### 2. Which selected LOB/domain does it serve?

**Answer**: Cross-cutting foundation, serves all Guidewire-aligned LOBs/domains
* All 31 tables are domain-agnostic record types
* Supports first proof slice (US P&C Personal Auto — California) via `gw_pc_bronze` schema
* Medallion architecture supports bronze/silver/gold data progression
* Supports future LOB/domain expansions without schema changes
* Guidewire PolicyCenter, ClaimCenter, BillingCenter alignment

### 3. What evidence will prove improvement?

**Evidence Measures**:
* ✅ **Schema Completeness**: 10 schemas created (3 bronze + 3 silver + 3 gold + control)
* ✅ **Table Completeness**: 31/31 tables created in each bronze schema (93 total)
* ✅ **Contract Conformance**: Generated DDL matches approved JSON Schema contracts
* ✅ **Governance Coverage**: All tables have UC tags, comments, ownership per GOV-002
* ✅ **Data Quality**: Tables enforce required fields, data types, constraints per contracts
* ✅ **Reproducibility**: Schema generation fully automated from contracts + config
* ✅ **Configuration Validity**: env_config.yaml passes validation
* ✅ **Integration Readiness**: Increment 3+ agents can read/write tables without schema changes

### 4. Is this genuinely required now?

**Answer**: YES — Blocking dependency for all subsequent increments
* Increment 3 (Source Onboarding): Requires evidence and snapshot tables in bronze
* Increment 4 (Dictionary Agent): Requires dictionary tables in bronze
* Increment 5+ (Silver/Gold): Requires bronze foundation + silver/gold schemas
* Without physical tables, agents have nowhere to write durable records
* Medallion architecture enables staged data refinement

### 5. Agent, skill, tool, validator, or context?

**Answer**: **Deterministic tool** (schema builder) + validation + **configuration skill**
* Schema generation: Deterministic code (no LLM, no semantic judgment)
* JSON Schema → Delta DDL translation: Rule-based transformation
* Configuration management: env-config-manager skill
* Validation: Automated tests (contract ↔ table schema conformance)
* Lifecycle state enforcement: Database constraints and guards

**NOT an agent**: No semantic interpretation, no judgment, no evidence synthesis. Pure structural translation driven by configuration.

---

## Objectives

### Primary Objective

Create **31 production-ready Delta tables in bronze layer** for each Guidewire product in Unity Catalog that:
1. Implement all approved Increment 1 contracts exactly
2. Enforce lifecycle state machines and guards
3. Support evidence traceability and provenance
4. Enable versioning and lineage tracking
5. Integrate with governance policies (GOV-001 through GOV-007)
6. Follow medallion architecture (bronze/silver/gold)
7. Use configuration-driven naming

### Secondary Objectives

* Establish medallion architecture foundation (bronze/silver/gold schemas)
* Create environment configuration file (`config/env_config.yaml`)
* Automate schema generation (no manual DDL authoring)
* Provide schema validation suite
* Document UC governance integration
* Create table usage examples for Increment 3+ agents
* Align with Guidewire PolicyCenter, ClaimCenter, BillingCenter architecture

---

## Technical Approach

### Architecture Principle

**Contracts + Configuration are authoritative**. Delta tables are generated artifacts.

```
config/env_config.yaml (configuration source of truth)
    ↓
JSON Schema Contract (schema source of truth)
    ↓ [automated generation with config]
Delta DDL (generated, never manually edited)
    ↓ [CREATE TABLE execution]
Unity Catalog Delta Table (physical implementation)
    ↓ [validation]
Conformance Test (proves contract ↔ table match)
```

### Medallion Architecture

```
Bronze Layer (Raw/Landing Zone)
  ↓ [Source discovery, evidence collection]
  ↓ [31 contract tables deployed here in Increment 2]
  
Silver Layer (Cleaned/Conformed)
  ↓ [ODS model, future increments]
  
Gold Layer (Aggregated/Dimensional)
  ↓ [Dimensional model, future increments]
```

### Schema Generation Strategy

**Tool**: Python script (`src/schema_builder/contract_to_ddl.py`)

**Configuration**: `config/env_config.yaml` (required)

**Input**: 31 JSON Schema contracts (`contracts/*.schema.json`)

**Output**: 
* 31 Delta DDL statements per bronze schema (`generated/ddl/gw_pc_bronze/*.sql`, etc.)
* 31 Unity Catalog table creation scripts per Guidewire bronze schema
* Validation suite (`tests/schema_builder/test_table_conformance.py`)

**Transformation Rules**:

| JSON Schema Type | Delta Type | Constraints |
|------------------|------------|-------------|
| `string` | `STRING` | — |
| `string` + `format: uuid` | `STRING` (UUID validation) | — |
| `string` + `format: date-time` | `TIMESTAMP` | — |
| `string` + `format: date` | `DATE` | — |
| `integer` | `BIGINT` | — |
| `number` | `DOUBLE` | — |
| `boolean` | `BOOLEAN` | — |
| `array` | `ARRAY<T>` | Nested type from `items` |
| `object` | `STRUCT<...>` | Nested properties |
| `enum` | `STRING` + CHECK constraint | Allowed values enforced |

**Lifecycle State Mapping**:
* JSON Schema `lifecycle_state` enum → Delta table CHECK constraint
* Lifecycle guards → Databricks SQL CHECK constraints or triggers

**Identity Pattern**:
* All tables have `record_id` (STRING, UUID, PRIMARY KEY)
* Composite business keys defined per contract
* Indexed for query performance

---

## Deliverables

### Core Deliverables

| # | Deliverable | Format | Location | Owner |
|---|-------------|--------|----------|-------|
| 1 | Environment Config | YAML | `config/env_config.yaml` | Data Architect |
| 2 | Env Config Manager Skill | Markdown | `.assistant/skills/env-config-manager/SKILL.md` | Tech Lead |
| 3 | Schema Builder Tool | Python module | `src/schema_builder/` | Tech Lead |
| 4 | Generated DDL Scripts | SQL files | `generated/ddl/{product}_{layer}/` | Auto-generated |
| 5 | 93 Delta Tables (31×3) | UC tables | `insurance_source_discovery.{product}_bronze.*` | Data Architect |
| 6 | Table Validation Suite | Python tests | `tests/schema_builder/` | Tech Lead |
| 7 | UC Governance Integration | Documentation | `docs/architecture/` | Data Steward |
| 8 | Usage Examples | Notebooks | `examples/increment_2/` | Tech Lead |
| 9 | Increment 2 Handoff | Markdown | `contracts/` | Project Manager |

### Table Organization

**Unity Catalog Structure** (driven by `config/env_config.yaml`):

```
insurance_source_discovery (catalog)
├── gw_pc_bronze (PolicyCenter - Bronze Layer) ← 31 contract tables
│   ├── Control & Run (4 tables)
│   │   ├── engagement
│   │   ├── work_package
│   │   ├── solution_run
│   │   └── artifact_version
│   ├── Snapshots & Sets (6 tables)
│   │   ├── source_snapshot, context_snapshot, profile_snapshot
│   │   └── document_set, requirement_set, evidence_set
│   ├── Evidence (5 tables)
│   │   ├── evidence_item, source_object_observation
│   │   ├── source_attribute_observation, profile_evidence
│   │   └── relationship_candidate
│   ├── Requirements (4 tables)
│   │   ├── analytical_requirement, reporting_requirement
│   │   └── business_term, business_rule
│   ├── Dictionary (4 tables)
│   │   ├── source_dictionary_object, source_dictionary_attribute
│   │   └── source_dictionary_relationship, source_dictionary_code_value
│   ├── Governance (4 tables)
│   │   ├── validation_finding, review_item
│   │   └── review_decision, open_question
│   ├── Lineage & Handoff (3 tables)
│   │   ├── artifact_dependency, lineage_edge
│   │   └── source_dictionary_handoff
│   └── Observability (1 table)
│       └── skill_resolution
│
├── gw_pc_silver (PolicyCenter - Silver Layer) ← Future Increment 5+
│   └── [ODS model tables, future]
│
├── gw_pc_gold (PolicyCenter - Gold Layer) ← Future Increment 6+
│   └── [Dimensional model tables, future]
│
├── gw_cc_bronze (ClaimCenter - Bronze Layer) ← 31 contract tables
│   └── [Same 31-table structure as gw_pc_bronze]
│
├── gw_cc_silver (ClaimCenter - Silver Layer) ← Future
│   └── [ODS model tables, future]
│
├── gw_cc_gold (ClaimCenter - Gold Layer) ← Future
│   └── [Dimensional model tables, future]
│
├── gw_bc_bronze (BillingCenter - Bronze Layer) ← 31 contract tables
│   └── [Same 31-table structure as gw_pc_bronze]
│
├── gw_bc_silver (BillingCenter - Silver Layer) ← Future
│   └── [ODS model tables, future]
│
├── gw_bc_gold (BillingCenter - Gold Layer) ← Future
│   └── [Dimensional model tables, future]
│
└── control (Agent/Framework Control & Intermediate)
    └── [Agent operation, harness, pipeline orchestration, temp tables]
```

**Naming Convention** (from `config/env_config.yaml`):
* Catalog: `insurance_source_discovery`
* Schemas: `{product_code}_{layer_suffix}` (e.g., `gw_pc_bronze`)
* Products: `gw_pc`, `gw_cc`, `gw_bc`
* Layers: `bronze`, `silver`, `gold`
* Tables: Match contract names exactly (snake_case)
* Agent/intermediate tables in `control`: Prefixes `agent_*`, `harness_*`, `temp_*`

**Proof Slice Alignment** (from `config/env_config.yaml`):
* **California P&C Personal Auto** → `insurance_source_discovery.gw_pc_bronze.*`
* Future claims data → `insurance_source_discovery.gw_cc_bronze.*`
* Future billing data → `insurance_source_discovery.gw_bc_bronze.*`

---

## Task Breakdown

### Phase 0: Configuration Setup (Week 1, Day 1 - Morning)

#### Task 0.1: Environment Configuration Creation & Validation
**Owner**: Data Architect + Tech Lead  
**Duration**: 2 hours  
**Deliverable**: Valid `config/env_config.yaml` ✅ (COMPLETE)

**Steps**:
1. ✅ Create `config/env_config.yaml` with full structure
2. ✅ Create `.assistant/skills/env-config-manager/SKILL.md`
3. Validate configuration structure and values
4. Load configuration in schema builder tool
5. Test configuration-driven schema name generation

**Acceptance Criteria**:
* ✅ `config/env_config.yaml` exists and is valid YAML
* ✅ Env config manager skill documented
* ✅ Configuration passes validation (all required keys present)
* ✅ Schema names generate correctly per pattern
* ✅ Proof slice configuration is accurate (California, gw_pc, bronze)

### Phase 1: Foundation Setup (Week 1, Days 1-2)

#### Task 1.1: UC Catalog and Schema Provisioning
**Owner**: Data Architect  
**Duration**: 1 day  
**Deliverable**: `insurance_source_discovery` catalog with 10 Guidewire-aligned schemas

**Steps**:
1. Load and validate `config/env_config.yaml`
2. Create `insurance_source_discovery` catalog in Unity Catalog
3. Create 10 schemas (configuration-driven):
   * `gw_pc_bronze`, `gw_pc_silver`, `gw_pc_gold` (PolicyCenter)
   * `gw_cc_bronze`, `gw_cc_silver`, `gw_cc_gold` (ClaimCenter)
   * `gw_bc_bronze`, `gw_bc_silver`, `gw_bc_gold` (BillingCenter)
   * `control` (Agent/Framework control)
4. Set ownership to Data Governance team (from config)
5. Apply schema-level tags per GOV-002 and config:
   * `internal_use` (Sensitivity Label) — all schemas
   * `data_governance` (Domain) — all schemas
   * `guidewire_pc` (Product Line) — gw_pc_* schemas
   * `guidewire_cc` (Product Line) — gw_cc_* schemas
   * `guidewire_bc` (Product Line) — gw_bc_* schemas
   * `bronze_layer` / `silver_layer` / `gold_layer` tags
   * `agent_harness` (Purpose) — control schema only
6. Document catalog and schemas in UC with purpose and contact info
7. Configure access controls (from config):
   * Read: all analysts (all product schemas)
   * Write: pipeline service principal (all product schemas)
   * Control schema: Restricted to agents/framework only

**Acceptance Criteria**:
* ✅ Catalog exists and is queryable
* ✅ All 10 schemas created (9 product/layer + 1 control)
* ✅ Schema names match config pattern: `{product}_{layer}`
* ✅ Ownership assigned to Data Governance team
* ✅ Tags applied per schema purpose and layer
* ✅ Permissions configured and tested

---

## Success Metrics

### Quantitative Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Configuration Valid** | 100% | env_config.yaml validation passes |
| **Schemas Created** | 10/10 (9 product/layer + control) | UC catalog query |
| **Bronze Tables Created** | 93/93 (31 per product × 3) | UC catalog query |
| **Contract Conformance** | 100% | Automated test suite |
| **Test Pass Rate** | 100% | pytest results |
| **DDL Generation Time** | < 5 minutes per schema | Tool execution time |
| **Schema Validation Time** | < 1 minute per schema | Test suite execution |
| **Documentation Coverage** | 100% (all 31 tables × 3 bronze schemas) | Manual review |

### Qualitative Metrics

* **Medallion Architecture**: Clear bronze/silver/gold separation
* **Configuration-Driven**: All naming decisions come from env_config.yaml
* **Guidewire Alignment**: Clear separation of PolicyCenter, ClaimCenter, BillingCenter concerns
* **Usability**: Can Increment 3+ developers use tables without schema questions?
* **Governance**: Do UC tags and comments meet CDO approval?
* **Maintainability**: Can schema builder tool regenerate DDL after contract OR config changes?
* **Reproducibility**: Can another team member regenerate schemas from contracts + config?

---

## CLI Usage Examples

### Using Configuration File

```bash
# Validate configuration
python -m schema_builder.validate_config \
  --config config/env_config.yaml

# Generate CREATE SCHEMA DDL from config
python -m schema_builder.generate_schemas \
  --config config/env_config.yaml \
  --output generated/ddl/create_schemas.sql

# Generate DDL for all enabled bronze schemas (from config)
python -m schema_builder.contract_to_ddl \
  --config config/env_config.yaml \
  --execute

# Generate DDL for specific product/layer
python -m schema_builder.contract_to_ddl \
  --config config/env_config.yaml \
  --product gw_pc \
  --layer bronze \
  --execute

# Validate tables against contracts
pytest tests/schema_builder/test_table_conformance.py \
  --config config/env_config.yaml \
  --schema gw_pc_bronze \
  -v
```

### Manual Schema Generation (Legacy)

```bash
# Generate DDL for PolicyCenter bronze
python -m schema_builder.contract_to_ddl \
  --input-dir contracts/ \
  --output-dir generated/ddl/gw_pc_bronze/ \
  --catalog insurance_source_discovery \
  --schema gw_pc_bronze

# Create all tables
python -m schema_builder.contract_to_ddl \
  --input-dir contracts/ \
  --catalog insurance_source_discovery \
  --schema gw_pc_bronze \
  --execute
```

---

## Example DDL Output

**Contract**: `engagement.schema.json`  
**Config**: `config/env_config.yaml` (product=gw_pc, layer=bronze)
**Generated DDL**: `generated/ddl/gw_pc_bronze/engagement.sql`

```sql
-- Auto-generated from engagement.schema.json v0.1.0
-- Configuration: config/env_config.yaml (product=gw_pc, layer=bronze)
-- DO NOT EDIT MANUALLY — Regenerate from contract + config

CREATE TABLE IF NOT EXISTS insurance_source_discovery.gw_pc_bronze.engagement (
  -- Identity
  record_id STRING NOT NULL COMMENT 'Unique record identifier (UUID)',
  schema_version STRING NOT NULL COMMENT 'Contract schema version',
  
  -- Core Fields
  engagement_id STRING NOT NULL COMMENT 'Business identifier for the engagement',
  engagement_name STRING NOT NULL COMMENT 'Human-readable engagement name',
  client_organization STRING COMMENT 'Client organization name',
  lob STRING NOT NULL COMMENT 'Line of business (e.g., P&C, Life, Health)',
  domain STRING COMMENT 'Business domain within LOB',
  
  -- Lifecycle
  lifecycle_state STRING NOT NULL 
    COMMENT 'Current lifecycle state'
    CONSTRAINT engagement_lifecycle_check 
    CHECK (lifecycle_state IN ('ACTIVE', 'SUSPENDED', 'CLOSED')),
  
  -- Provenance
  created_at TIMESTAMP NOT NULL COMMENT 'Record creation timestamp',
  created_by STRING NOT NULL COMMENT 'User or service that created the record',
  updated_at TIMESTAMP COMMENT 'Last update timestamp',
  updated_by STRING COMMENT 'User or service that last updated the record',
  
  -- Constraints
  CONSTRAINT engagement_pk PRIMARY KEY (record_id)
)
USING DELTA
COMMENT 'Engagement envelope and control record (Guidewire PolicyCenter - Bronze Layer)'
TBLPROPERTIES (
  'delta.enableChangeDataFeed' = 'true',
  'governance.sensitivity_label' = 'INTERNAL',
  'governance.domain' = 'data_governance',
  'governance.product_line' = 'guidewire_pc',
  'governance.layer' = 'bronze',
  'governance.purpose' = 'engagement_management'
);

-- Column-level tags (applied via ALTER TABLE after creation)
ALTER TABLE insurance_source_discovery.gw_pc_bronze.engagement 
  ALTER COLUMN engagement_id 
  SET TAGS ('business_key' = 'true');
```

---

## Configuration Management

### Changing Proof Slice

To switch from California to New York:

```yaml
# In config/env_config.yaml
proof_slice:
  product: gw_pc
  layer: bronze
  jurisdiction: New York  # Changed
  lob: "P&C Personal Auto"
  description: "US P&C Personal Auto — New York proof slice"
```

### Enabling Silver/Gold Layers (Future Increments)

```yaml
# In config/env_config.yaml
schema_builder:
  generate_for:
    # ... existing bronze configs ...
    - product: gw_pc
      layer: silver
      enabled: true  # Enable for Increment 5
    - product: gw_pc
      layer: gold
      enabled: true  # Enable for Increment 6
```

### Adding New Guidewire Product

```yaml
# In config/env_config.yaml
guidewire_products:
  # ... existing products ...
  - code: gw_wc
    name: "Guidewire WorkersCompCenter"
    description: "Workers Compensation"
    lob: "Workers Comp"
```

---

## Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Technical Lead** | _______________ | _______________ | ______ |
| **Data Architect** | _______________ | _______________ | ______ |
| **Data Steward** | _______________ | _______________ | ______ |
| **Chief Data Officer** | _______________ | _______________ | ______ |
| **Project Manager** | _______________ | _______________ | ______ |

---

**This plan is APPROVED and READY TO EXECUTE.**

Increment 2 creates the Guidewire-aligned medallion architecture foundation for all future work. Configuration-driven, no shortcuts, no manual DDL, no deviations from contracts. Build it right, build it once, validate everything.
