"""
Type mapping from JSON Schema to Delta/Spark SQL types.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .ref_resolver import RefResolver


class TypeMapper:
    """Maps JSON Schema types to Delta SQL types."""
    
    # Base type mappings
    TYPE_MAP = {
        'string': 'STRING',
        'integer': 'BIGINT',
        'number': 'DOUBLE',
        'boolean': 'BOOLEAN'
    }
    
    # Format-specific mappings
    FORMAT_MAP = {
        'uuid': 'STRING',  # UUID stored as STRING
        'date-time': 'TIMESTAMP',
        'date': 'DATE',
        'time': 'STRING',  # TIME stored as STRING (no native TIME type)
        'email': 'STRING',
        'uri': 'STRING',
        'hostname': 'STRING'
    }
    
    def __init__(self, ref_resolver: Optional['RefResolver'] = None):
        """
        Initialize TypeMapper with optional RefResolver for handling $ref fields.
        
        Args:
            ref_resolver: RefResolver instance for resolving $ref in property schemas
        """
        self.ref_resolver = ref_resolver
    
    def map_type(self, json_schema: Dict[str, Any], property_name: str = None) -> str:
        """
        Map a JSON Schema property to a Delta SQL type.
        
        Args:
            json_schema: The JSON Schema property definition
            property_name: Optional property name for context
            
        Returns:
            Delta SQL type string
        """
        # Handle $ref by resolving it first
        if '$ref' in json_schema:
            if self.ref_resolver is None:
                raise ValueError(
                    f"Cannot resolve $ref '{json_schema['$ref']}' without RefResolver. "
                    "Pass a RefResolver instance to TypeMapper constructor."
                )
            # Resolve the $ref and map the resolved schema
            resolved_schema = self.ref_resolver.resolve(json_schema)
            return self.map_type(resolved_schema, property_name)
        
        # Handle arrays
        if json_schema.get('type') == 'array':
            return self._map_array(json_schema)
        
        # Handle objects
        if json_schema.get('type') == 'object':
            return self._map_object(json_schema)
        
        # Handle enums (stored as STRING with CHECK constraint)
        if 'enum' in json_schema:
            return 'STRING'
        
        # Get base type
        json_type = json_schema.get('type')
        if not json_type:
            # If no type specified, default to STRING
            return 'STRING'
        
        # Check for format override
        json_format = json_schema.get('format')
        if json_format and json_format in self.FORMAT_MAP:
            return self.FORMAT_MAP[json_format]
        
        # Use base type mapping
        if json_type in self.TYPE_MAP:
            return self.TYPE_MAP[json_type]
        
        # Fallback to STRING
        return 'STRING'
    
    def _map_array(self, json_schema: Dict[str, Any]) -> str:
        """Map an array type."""
        items_schema = json_schema.get('items', {})
        
        # Handle empty items (any type)
        if not items_schema:
            return 'ARRAY<STRING>'
        
        # Get item type (recursively handles $ref in items)
        item_type = self.map_type(items_schema)
        
        return f'ARRAY<{item_type}>'
    
    def _map_object(self, json_schema: Dict[str, Any]) -> str:
        """Map an object type to STRUCT."""
        properties = json_schema.get('properties', {})
        
        if not properties:
            # Empty struct
            return 'STRUCT<>'
        
        # Build struct fields (recursively handles $ref in properties)
        fields = []
        for prop_name, prop_schema in properties.items():
            prop_type = self.map_type(prop_schema, prop_name)
            fields.append(f'{prop_name}: {prop_type}')
        
        return f"STRUCT<{', '.join(fields)}>"
    
    def get_enum_values(self, json_schema: Dict[str, Any]) -> Optional[List[str]]:
        """
        Extract enum values if present.
        
        Handles $ref by resolving first if needed.
        """
        # Resolve $ref if present
        if '$ref' in json_schema and self.ref_resolver:
            json_schema = self.ref_resolver.resolve(json_schema)
        
        return json_schema.get('enum')
    
    def is_nullable(self, json_schema: Dict[str, Any], required_fields: List[str], 
                   property_name: str) -> bool:
        """
        Determine if a field is nullable.
        
        Args:
            json_schema: The property schema
            required_fields: List of required field names from parent schema
            property_name: Name of this property
            
        Returns:
            True if nullable (NOT NULL not needed)
        """
        # Resolve $ref if present
        if '$ref' in json_schema and self.ref_resolver:
            json_schema = self.ref_resolver.resolve(json_schema)
        
        # Check if in required list
        if property_name in required_fields:
            return False
        
        # Check for explicit nullable
        if 'nullable' in json_schema:
            return json_schema['nullable']
        
        # Default to nullable for optional fields
        return True
