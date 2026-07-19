# Skill: Environment Configuration Manager

**Version**: 1.0.0  
**Status**: Active  
**Purpose**: Manage Unity Catalog structure and naming conventions via `config/env_config.yaml`

## Overview

This skill provides guidance for working with the environment configuration file that drives Unity Catalog schema naming, access control, and DDL generation for the Agentic Data Modeling Studio.

## Key Principles

1. **Configuration is authoritative**: All catalog, schema, and table organization is defined in `config/env_config.yaml`
2. **Separation of concerns**: Contract tables (agent framework) go to `control` schema; source data goes to product bronze/silver/gold schemas
3. **Medallion architecture**: Bronze (raw source) → Silver (ODS) → Gold (dimensional) per Guidewire product
4. **No code changes for structure**: Adding products, layers, or changing access requires only config updates

## Configuration Structure

### Catalog Definition
```yaml
catalog:
  name: insurance_source_discovery
  description: "Insurance source data discovery and reconstruction system"
  owner: "Data Governance Team"
```

### Guidewire Products
Three Guidewire product lines are supported:
- `gw_pc`: PolicyCenter (P&C Insurance)
- `gw_cc`: ClaimCenter (Claims Processing)
- `gw_bc`: BillingCenter (Billing & Payments)

### Schema Types

#### Product Schemas (Medallion Pattern)
Format: `{product_code}_{layer_suffix}`

**Bronze Layer** (`*_bronze`):
- Purpose: Raw/landing zone for source system data
- Contains: Actual source data from PolicyCenter, ClaimCenter, BillingCenter
- `tables_from_contracts: false` (source data only)

**Silver Layer** (`*_silver`):
- Purpose: Cleaned, conformed, ODS
- Contains: Silver ODS model, cleaned entities
- Future increment

**Gold Layer** (`*_gold`):
- Purpose: Aggregated, dimensional model
- Contains: Business-ready analytics tables
- Future increment

#### Control Schema
Schema name: `control`
- Purpose: Agent/framework operations and contract tables
- Contains: **All 29 run-rooted contract tables** (solution_run, evidence_item, source_dictionary_*, etc.)
- `tables_from_contracts: true` (the 29 contract tables go here)
- Tags: `agent_harness`, `internal_use`, `contract_tables`

### Complete Schema Structure

```
insurance_source_discovery/
├── control/                          ← 29 run-rooted contract tables
│   ├── solution_run
│   ├── work_package
│   ├── solution_run
│   ├── artifact_version
│   ├── source_snapshot
│   ├── context_snapshot
│   ├── profile_snapshot
│   ├── document_set
│   ├── requirement_set
│   ├── evidence_set
│   ├── evidence_item
│   ├── source_object_observation
│   ├── source_attribute_observation
│   ├── profile_evidence
│   ├── relationship_candidate
│   ├── analytical_requirement
│   ├── reporting_requirement
│   ├── business_term
│   ├── business_rule
│   ├── source_dictionary_object
│   ├── source_dictionary_attribute
│   ├── source_dictionary_relationship
│   ├── source_dictionary_code_value
│   ├── validation_finding
│   ├── review_item
│   ├── review_decision
│   ├── open_question
│   ├── artifact_dependency
│   ├── lineage_edge
│   ├── source_dictionary_handoff
│   └── skill_resolution
│
├── gw_pc_bronze/                     ← PolicyCenter source data (future)
├── gw_pc_silver/                     ← PolicyCenter ODS (future)
├── gw_pc_gold/                       ← PolicyCenter dimensional (future)
│
├── gw_cc_bronze/                     ← ClaimCenter source data (future)
├── gw_cc_silver/                     ← ClaimCenter ODS (future)
├── gw_cc_gold/                       ← ClaimCenter dimensional (future)
│
├── gw_bc_bronze/                     ← BillingCenter source data (future)
├── gw_bc_silver/                     ← BillingCenter ODS (future)
└── gw_bc_gold/                       ← BillingCenter dimensional (future)
```

## Schema Builder Configuration

DDL generation is controlled by the `schema_builder.generate_for` section:

```yaml
schema_builder:
  generate_for:
    - schema: control
      layer: control
      enabled: true              # Increment 2: Generate 29 contract tables here
      description: "29 run-rooted contract tables for agent framework"
    
    - product: gw_pc
      layer: bronze
      enabled: false             # Future: Will contain source data
```

## Access Control

### Read Access
- **Principals**: `all_analysts`
- **Schemas**: All product bronze/silver/gold schemas
- **Purpose**: Query source and modeled data

### Write Access
- **Principals**: `pipeline_service_principal`
- **Schemas**: All product bronze/silver/gold schemas
- **Purpose**: ETL/pipeline writes

### Control Access
- **Principals**: `agent_framework`, `harness_service_principal`
- **Schemas**: `control` only
- **Purpose**: Agent framework operations

## Common Operations

### Reading Configuration
```python
import yaml

with open("config/env_config.yaml") as f:
    config = yaml.safe_load(f)

catalog_name = config["catalog"]["name"]
control_schema = config["control_schema"]["name"]
```

### Generating Schema Names
```python
def get_product_schema_name(product_code: str, layer: str) -> str:
    """Generate schema name per pattern: {product_code}_{layer_suffix}"""
    return f"{product_code}_{layer}"

# Examples:
# get_product_schema_name("gw_pc", "bronze") → "gw_pc_bronze"
# get_product_schema_name("gw_cc", "silver") → "gw_cc_silver"
```

### Checking Where Tables Belong
```python
def should_generate_in_schema(config: dict, schema_name: str) -> bool:
    """Check if DDL should be generated for a schema"""
    
    # Contract tables go to control schema
    if schema_name == config["control_schema"]["name"]:
        return config["control_schema"]["tables_from_contracts"]
    
    # Product schemas (bronze/silver/gold) get source data, not contracts
    for layer in config["layers"].values():
        if schema_name.endswith(f"_{layer['suffix']}"):
            return layer.get("tables_from_contracts", False)
    
    return False
```

## Governance Integration

All schemas receive governance tags per GOV-002:
- **Sensitivity labels**: INTERNAL, CONFIDENTIAL, RESTRICTED, PUBLIC
- **Domains**: data_governance, source_discovery, modeling, analytics
- **Product lines**: guidewire_pc, guidewire_cc, guidewire_bc

Control schema receives additional tags:
- `agent_harness: true`
- `contract_tables: true`

## Validation Rules

When modifying `env_config.yaml`:

1. **Catalog name** must be a valid Unity Catalog identifier
2. **Product codes** must be unique and match pattern `gw_[a-z]+`
3. **Schema naming pattern** must produce valid schema names
4. **Control schema** must have `tables_from_contracts: true`
5. **Layer schemas** (bronze/silver/gold) must have `tables_from_contracts: false`
6. **Access control** principals must exist in the workspace
7. **DDL generation** can only enable one schema for contract tables

## Common Mistakes to Avoid

❌ **Wrong**: Contract tables in bronze schemas
```yaml
layers:
  bronze:
    tables_from_contracts: true  # WRONG! Bronze is for source data
```

✅ **Correct**: Contract tables in control schema
```yaml
control_schema:
  tables_from_contracts: true   # Correct! Framework tables here
```

❌ **Wrong**: Mixed purposes in one schema
```yaml
# Don't mix contract tables and source data in the same schema
```

✅ **Correct**: Clear separation
- Control schema = Contract tables (agent framework)
- Bronze schemas = Source data (PolicyCenter, ClaimCenter, BillingCenter)

## Migration from Old Architecture

If contract tables were previously created in bronze schemas:

1. Read `env_config.yaml` to confirm new architecture
2. Create tables in `control` schema from contracts
3. Migrate any data from old bronze contract tables to control
4. Drop old contract tables from bronze schemas
5. Update all references to use `control` schema

## References

- Main config file: `config/env_config.yaml`
- Implementation plan: `docs/architecture/INCREMENT_2_SCHEMA_BUILDER_IMPLEMENTATION_PLAN.md`
- Contract inventory: `contracts/CONTRACT_INVENTORY.md`
- Governance policies: GOV-001 through GOV-007
