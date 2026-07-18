"""
DDL generation from JSON Schema contracts.
"""

from typing import Dict, Any, List, Optional
from .type_mapper import TypeMapper
from .config_loader import ConfigLoader
from .ref_resolver import RefResolver


class DDLGenerator:
    """Generate Delta table DDL from JSON Schema contracts."""
    
    def __init__(self, config_loader: Optional[ConfigLoader] = None, 
                 contracts_dir: str = "contracts"):
        self.config_loader = config_loader
        self.ref_resolver = RefResolver(contracts_dir)
        # Pass ref_resolver to TypeMapper so it can resolve $ref in properties
        self.type_mapper = TypeMapper(ref_resolver=self.ref_resolver)
        
    def generate(self, contract: Dict[str, Any], catalog: str, schema: str, 
                 table_name: Optional[str] = None) -> str:
        """
        Generate CREATE TABLE DDL from a JSON Schema contract.
        
        Returns both the CREATE TABLE statement and separate ALTER TABLE statements
        for CHECK constraints (since Databricks doesn't support inline CHECK).
        
        Args:
            contract: Parsed JSON Schema contract (may contain $ref and allOf)
            catalog: Unity Catalog catalog name
            schema: Schema name
            table_name: Override table name (defaults to contract title)
            
        Returns:
            SQL DDL string with CREATE TABLE and ALTER TABLE statements
        """
        # Resolve all $ref and flatten allOf compositions
        resolved_contract = self.ref_resolver.resolve(contract)
        
        # Extract metadata from resolved contract
        metadata = self.ref_resolver.get_table_metadata(resolved_contract)
        title = table_name or metadata['title']
        description = metadata['description']
        version = metadata['version']
        
        # Get properties and required fields from resolved schema
        properties = resolved_contract.get('properties', {})
        required_fields = resolved_contract.get('required', [])
        
        # Generate column definitions
        columns = self._generate_columns(properties, required_fields)
        
        # Generate PRIMARY KEY constraint (pass actual table name)
        pk_constraint = self._generate_pk_constraint(properties, title)
        
        # Generate CHECK constraints (to be added via ALTER TABLE)
        check_constraints = self._generate_check_constraints(properties, title, catalog, schema)
        
        # Build CREATE TABLE DDL
        ddl_lines = []
        
        # Header comment
        ddl_lines.append(f"-- Auto-generated from {title}.schema.json v{version}")
        if self.config_loader:
            ddl_lines.append(f"-- Configuration: config/env_config.yaml (schema={schema})")
        ddl_lines.append("-- DO NOT EDIT MANUALLY — Regenerate from contract + config")
        ddl_lines.append("")
        
        # CREATE TABLE statement
        full_table_name = f"{catalog}.{schema}.{title}"
        ddl_lines.append(f"CREATE TABLE IF NOT EXISTS {full_table_name} (")
        
        # Add columns
        ddl_lines.extend([f"  {col}," for col in columns])
        
        # Add PRIMARY KEY constraint if present
        if pk_constraint:
            ddl_lines.append("")
            ddl_lines.append("  -- Constraints")
            ddl_lines.append(f"  {pk_constraint}")
        
        # Remove trailing comma from last line
        if ddl_lines[-1].endswith(','):
            ddl_lines[-1] = ddl_lines[-1][:-1]
        
        ddl_lines.append(")")
        ddl_lines.append("USING DELTA")
        
        # Add table comment
        if description:
            ddl_lines.append(f"COMMENT '{self._escape_sql_string(description)}'")
        
        # Add table properties
        ddl_lines.extend(self._generate_table_properties(schema))
        
        ddl_lines.append(";")
        
        # Add ALTER TABLE statements for CHECK constraints
        if check_constraints:
            ddl_lines.append("")
            ddl_lines.append("-- CHECK constraints added via ALTER TABLE")
            ddl_lines.extend(check_constraints)
        
        return "\n".join(ddl_lines)
    
    def _generate_columns(self, properties: Dict[str, Any], 
                         required_fields: List[str]) -> List[str]:
        """Generate column definitions."""
        columns = []
        
        for prop_name, prop_schema in properties.items():
            # Get Delta type
            delta_type = self.type_mapper.map_type(prop_schema, prop_name)
            
            # Nullable?
            nullable = self.type_mapper.is_nullable(prop_schema, required_fields, prop_name)
            not_null = "" if nullable else "NOT NULL"
            
            # Comment
            comment = prop_schema.get('description', '')
            comment_clause = f"COMMENT '{self._escape_sql_string(comment)}'" if comment else ""
            
            # Build column definition
            parts = [prop_name, delta_type, not_null, comment_clause]
            col_def = " ".join([p for p in parts if p])
            
            columns.append(col_def)
        
        return columns
    
    def _generate_pk_constraint(self, properties: Dict[str, Any], 
                               table_name: str) -> Optional[str]:
        """
        Generate PRIMARY KEY constraint.
        
        Args:
            properties: Table properties dict
            table_name: Actual table name for constraint naming
        """
        # PRIMARY KEY on record_id if it exists
        if 'record_id' in properties:
            # Use actual table name in constraint name
            return f"CONSTRAINT {table_name}_pk PRIMARY KEY (record_id)"
        return None
    
    def _generate_check_constraints(self, properties: Dict[str, Any], 
                                   table_name: str, catalog: str, schema: str) -> List[str]:
        """
        Generate ALTER TABLE statements for CHECK constraints.
        
        Databricks doesn't support inline CHECK constraints, so we generate
        separate ALTER TABLE ADD CONSTRAINT statements.
        """
        constraints = []
        full_table_name = f"{catalog}.{schema}.{table_name}"
        
        for prop_name, prop_schema in properties.items():
            enum_values = self.type_mapper.get_enum_values(prop_schema)
            
            if enum_values:
                # Generate ALTER TABLE ADD CONSTRAINT for enum
                values_list = ", ".join([f"'{v}'" for v in enum_values])
                constraint_name = f"{table_name}_{prop_name}_check"
                alter_stmt = (
                    f"ALTER TABLE {full_table_name} "
                    f"ADD CONSTRAINT {constraint_name} "
                    f"CHECK ({prop_name} IN ({values_list}));"
                )
                constraints.append(alter_stmt)
        
        return constraints
    
    def _generate_table_properties(self, schema: str) -> List[str]:
        """Generate TBLPROPERTIES clause."""
        props = []
        props.append("TBLPROPERTIES (")
        props.append("  'delta.enableChangeDataFeed' = 'true',")
        props.append("  'governance.sensitivity_label' = 'INTERNAL',")
        props.append("  'governance.domain' = 'data_governance',")
        
        # Add product and layer tags based on schema name
        if 'gw_pc' in schema:
            props.append("  'governance.product_line' = 'guidewire_pc',")
        elif 'gw_cc' in schema:
            props.append("  'governance.product_line' = 'guidewire_cc',")
        elif 'gw_bc' in schema:
            props.append("  'governance.product_line' = 'guidewire_bc',")
        
        if 'bronze' in schema:
            props.append("  'governance.layer' = 'bronze',")
        elif 'silver' in schema:
            props.append("  'governance.layer' = 'silver',")
        elif 'gold' in schema:
            props.append("  'governance.layer' = 'gold',")
        
        props.append("  'governance.purpose' = 'source_data_discovery'")
        props.append(")")
        
        return props
    
    def _escape_sql_string(self, s: str) -> str:
        """Escape single quotes in SQL strings."""
        return s.replace("'", "''")
