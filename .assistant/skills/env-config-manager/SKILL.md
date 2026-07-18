# Skill: Environment Configuration Manager

## Purpose
Load, validate, and apply Unity Catalog environment configuration from `config/env_config.yaml`.

## When to Use
* Before creating Unity Catalog schemas
* Before running schema builder tool
* When validating catalog/schema naming
* When generating DDL for specific product/layer
* When setting up governance tags and access controls

## Configuration Structure

### Catalog
* Name, description, owner
* Root-level tags

### Guidewire Products
* `gw_pc`, `gw_cc`, `gw_bc`
* Product name, description, LOB

### Medallion Layers
* `bronze`: Raw/landing zone (31 contract tables)
* `silver`: Cleaned, conformed ODS (future)
* `gold`: Dimensional model (future)

### Schema Naming Pattern
`{product_code}_{layer_suffix}`

Examples:
* `gw_pc_bronze` — PolicyCenter bronze layer
* `gw_cc_silver` — ClaimCenter silver layer
* `gw_bc_gold` — BillingCenter gold layer
* `control` — Agent/framework control

### Proof Slice
First implementation target:
* Product: `gw_pc`
* Layer: `bronze`
* Jurisdiction: California
* LOB: P&C Personal Auto

## Usage

### 1. Load Configuration

```python
import yaml

def load_env_config(config_path="config/env_config.yaml"):
    """Load and parse environment configuration."""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

config = load_env_config()
```

### 2. Get Schema Names

```python
def get_schema_names(config, include_control=True):
    """Generate all schema names from config."""
    schemas = []
    
    # Generate product/layer schemas
    for product in config['guidewire_products']:
        for layer_name, layer_config in config['layers'].items():
            schema_name = f"{product['code']}_{layer_config['suffix']}"
            schemas.append({
                'name': schema_name,
                'product': product['code'],
                'product_name': product['name'],
                'layer': layer_name,
                'description': f"{product['name']} - {layer_config['description']}",
                'purpose': layer_config['purpose']
            })
    
    # Add control schema
    if include_control:
        schemas.append({
            'name': config['control_schema']['name'],
            'product': None,
            'product_name': 'Control',
            'layer': None,
            'description': config['control_schema']['description'],
            'purpose': config['control_schema']['purpose']
        })
    
    return schemas

schemas = get_schema_names(config)
for schema in schemas:
    print(f"{schema['name']}: {schema['description']}")
```

### 3. Get Target Schema for Increment

```python
def get_current_target_schema(config):
    """Get the schema for the current increment's proof slice."""
    proof = config['proof_slice']
    layer_suffix = config['layers'][proof['layer']]['suffix']
    schema_name = f"{proof['product']}_{layer_suffix}"
    
    return {
        'schema': schema_name,
        'catalog': config['catalog']['name'],
        'full_name': f"{config['catalog']['name']}.{schema_name}",
        'jurisdiction': proof['jurisdiction'],
        'lob': proof['lob'],
        'description': proof['description']
    }

target = get_current_target_schema(config)
print(f"Current target: {target['full_name']}")
print(f"Proof slice: {target['description']}")
```

### 4. Generate CREATE SCHEMA Statements

```python
def generate_create_schema_sql(config):
    """Generate SQL to create all schemas."""
    catalog_name = config['catalog']['name']
    statements = []
    
    # Create catalog
    statements.append(f"""
CREATE CATALOG IF NOT EXISTS {catalog_name}
COMMENT '{config['catalog']['description']}';
""")
    
    # Create schemas
    schemas = get_schema_names(config)
    for schema in schemas:
        schema_name = schema['name']
        full_name = f"{catalog_name}.{schema_name}"
        
        sql = f"""
CREATE SCHEMA IF NOT EXISTS {full_name}
COMMENT '{schema['description']}';

-- Set ownership
ALTER SCHEMA {full_name} OWNER TO `{config['catalog']['owner']}`;
"""
        statements.append(sql)
    
    return '\n'.join(statements)

ddl = generate_create_schema_sql(config)
print(ddl)
```

### 5. Validate Configuration

```python
def validate_config(config):
    """Validate configuration structure and values."""
    errors = []
    
    # Check required top-level keys
    required_keys = ['catalog', 'guidewire_products', 'layers', 
                     'control_schema', 'schema_naming', 'proof_slice']
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")
    
    # Validate proof slice references
    if 'proof_slice' in config:
        proof = config['proof_slice']
        
        # Check product exists
        valid_products = [p['code'] for p in config.get('guidewire_products', [])]
        if proof.get('product') not in valid_products:
            errors.append(f"Proof slice product '{proof.get('product')}' not in guidewire_products")
        
        # Check layer exists
        if proof.get('layer') not in config.get('layers', {}):
            errors.append(f"Proof slice layer '{proof.get('layer')}' not in layers")
    
    # Check schema naming pattern
    if 'schema_naming' in config:
        pattern = config['schema_naming'].get('pattern', '')
        if '{product_code}' not in pattern or '{layer_suffix}' not in pattern:
            errors.append("Schema naming pattern must include {product_code} and {layer_suffix}")
    
    return errors

errors = validate_config(config)
if errors:
    print("❌ Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("✅ Configuration is valid")
```

### 6. Get Schemas for DDL Generation

```python
def get_enabled_schemas_for_generation(config):
    """Get schemas that are enabled for DDL generation."""
    enabled = []
    
    for gen_config in config['schema_builder']['generate_for']:
        if gen_config.get('enabled', False):
            product = gen_config['product']
            layer = gen_config['layer']
            layer_suffix = config['layers'][layer]['suffix']
            schema_name = f"{product}_{layer_suffix}"
            
            enabled.append({
                'schema': schema_name,
                'product': product,
                'layer': layer,
                'catalog': config['catalog']['name'],
                'output_dir': f"{config['schema_builder']['output_base_dir']}{schema_name}/"
            })
    
    return enabled

enabled_schemas = get_enabled_schemas_for_generation(config)
print(f"Enabled for DDL generation:")
for schema in enabled_schemas:
    print(f"  - {schema['catalog']}.{schema['schema']} -> {schema['output_dir']}")
```

## Integration with Schema Builder

The schema builder tool should:

1. **Load config at startup**
```python
config = load_env_config()
```

2. **Validate before proceeding**
```python
errors = validate_config(config)
if errors:
    raise ValueError(f"Config validation failed: {errors}")
```

3. **Get target schemas**
```python
enabled_schemas = get_enabled_schemas_for_generation(config)
for schema_config in enabled_schemas:
    generate_ddl_for_schema(schema_config)
```

4. **Use naming conventions**
```python
catalog_name = config['catalog']['name']
schema_name = f"{product_code}_{layer_suffix}"
table_name = contract_name  # from JSON Schema filename
full_table_name = f"{catalog_name}.{schema_name}.{table_name}"
```

## CLI Integration

### Generate Schema DDL from Config

```bash
# Load config and generate CREATE SCHEMA statements
python -m schema_builder.generate_schemas \
  --config config/env_config.yaml \
  --output generated/ddl/create_schemas.sql

# Validate configuration
python -m schema_builder.validate_config \
  --config config/env_config.yaml

# Generate DDL for all enabled schemas
python -m schema_builder.contract_to_ddl \
  --config config/env_config.yaml \
  --execute
```

## Configuration Management

### Update Proof Slice

To change the proof slice (e.g., from California to New York):

```yaml
# In config/env_config.yaml
proof_slice:
  product: gw_pc
  layer: bronze
  jurisdiction: New York  # Changed
  lob: "P&C Personal Auto"
  description: "US P&C Personal Auto — New York proof slice"
```

### Enable Silver/Gold Layers

When ready for Increment 5+:

```yaml
# In config/env_config.yaml
schema_builder:
  generate_for:
    # ... existing bronze configs ...
    - product: gw_pc
      layer: silver
      enabled: true  # Enable silver layer
    - product: gw_pc
      layer: gold
      enabled: true  # Enable gold layer
```

### Add New Guidewire Product

```yaml
# In config/env_config.yaml
guidewire_products:
  # ... existing products ...
  - code: gw_wc
    name: "Guidewire WorkersCompCenter"
    description: "Workers Compensation"
    lob: "Workers Comp"
```

## Governance Integration

The config defines:
* Sensitivity labels (GOV-002)
* Access control principals
* Product line tags
* Schema-level tags

Schema builder applies these during table creation.

## Best Practices

1. **Always validate config before use**
   ```python
   errors = validate_config(config)
   if errors: raise ValueError(errors)
   ```

2. **Use config for ALL naming decisions**
   Never hard-code catalog/schema names in code

3. **Version control env_config.yaml**
   Track changes, use PRs for config updates

4. **Document config changes**
   Add comments explaining why values changed

5. **Test config changes in dev first**
   Validate in dev environment before prod

## Error Handling

```python
try:
    config = load_env_config()
    errors = validate_config(config)
    if errors:
        raise ValueError(f"Invalid configuration: {'; '.join(errors)}")
except FileNotFoundError:
    raise FileNotFoundError("config/env_config.yaml not found. Run setup first.")
except yaml.YAMLError as e:
    raise ValueError(f"YAML parse error in env_config.yaml: {e}")
```

## Future Extensions

* Environment-specific configs (dev/staging/prod)
* Dynamic schema generation based on LOB metadata
* Config validation against JSON Schema
* Config migration tools for version upgrades
