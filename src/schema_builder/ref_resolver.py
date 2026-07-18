"""
JSON Schema $ref resolver with allOf composition support.
Resolves URN-based references and flattens schema composition.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse


class RefResolver:
    """Resolve JSON Schema $ref and flatten allOf compositions."""
    
    def __init__(self, contracts_dir: str = "contracts"):
        self.contracts_dir = Path(contracts_dir)
        self.schemas_cache = {}  # Cache loaded schemas by URN
        self.current_schema_urn = None  # Track current schema context for relative refs
        self._load_common_schema()
    
    def _load_common_schema(self):
        """Pre-load the common schema for envelope and lifecycle definitions."""
        common_path = self.contracts_dir / "_common.schema.json"
        
        if not common_path.exists():
            raise FileNotFoundError(f"_common.schema.json not found at {common_path}")
        
        with open(common_path, 'r') as f:
            common_schema = json.load(f)
        
        # Cache by URN
        schema_id = common_schema.get('$id')
        if schema_id:
            self.schemas_cache[schema_id] = common_schema
    
    def resolve(self, schema: Dict[str, Any], context_urn: Optional[str] = None) -> Dict[str, Any]:
        """
        Resolve all $ref and flatten allOf compositions in a schema.
        
        Args:
            schema: The JSON Schema to resolve
            context_urn: The URN of the schema context (for resolving relative refs)
            
        Returns:
            Fully resolved schema with all references expanded
        """
        # Save previous context and set new one if provided
        previous_urn = self.current_schema_urn
        if context_urn:
            self.current_schema_urn = context_urn
        
        try:
            # If schema has allOf, merge all schemas
            if 'allOf' in schema:
                return self._resolve_all_of(schema)
            
            # If schema has $ref, resolve it
            if '$ref' in schema:
                return self._resolve_ref(schema['$ref'])
            
            # Recursively resolve any nested $refs in properties
            if 'properties' in schema:
                schema = dict(schema)  # Make a copy
                schema['properties'] = self._resolve_properties(schema['properties'])
            
            # Otherwise return
            return schema
        finally:
            # Restore previous context
            self.current_schema_urn = previous_urn
    
    def _resolve_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively resolve $refs in a properties dict."""
        resolved = {}
        for prop_name, prop_schema in properties.items():
            if isinstance(prop_schema, dict):
                if '$ref' in prop_schema:
                    # Resolve the $ref
                    resolved[prop_name] = self.resolve(prop_schema)
                else:
                    # Check if it has nested properties
                    if 'properties' in prop_schema:
                        prop_schema = dict(prop_schema)
                        prop_schema['properties'] = self._resolve_properties(prop_schema['properties'])
                    # Check for oneOf/anyOf/allOf
                    if 'oneOf' in prop_schema:
                        prop_schema = dict(prop_schema)
                        prop_schema['oneOf'] = [self.resolve(s) for s in prop_schema['oneOf']]
                    if 'anyOf' in prop_schema:
                        prop_schema = dict(prop_schema)
                        prop_schema['anyOf'] = [self.resolve(s) for s in prop_schema['anyOf']]
                    resolved[prop_name] = prop_schema
            else:
                resolved[prop_name] = prop_schema
        return resolved
    
    def _resolve_all_of(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flatten an allOf composition.
        Merges properties and required fields from all schemas.
        """
        all_of = schema.get('allOf', [])
        
        # Start with base schema (everything except allOf)
        merged = {k: v for k, v in schema.items() if k != 'allOf'}
        
        # Initialize properties and required if not present
        if 'properties' not in merged:
            merged['properties'] = {}
        if 'required' not in merged:
            merged['required'] = []
        
        # Merge each schema in allOf
        for sub_schema in all_of:
            resolved_sub = self.resolve(sub_schema)
            
            # Merge properties
            if 'properties' in resolved_sub:
                merged['properties'].update(resolved_sub['properties'])
            
            # Merge required fields
            if 'required' in resolved_sub:
                for field in resolved_sub['required']:
                    if field not in merged['required']:
                        merged['required'].append(field)
            
            # Merge metadata keys (title, description, version) - first non-null wins
            for key in ['title', 'description', 'version']:
                if key in resolved_sub and key not in merged:
                    merged[key] = resolved_sub[key]
            
            # Merge other keys (type, etc.)
            # Skip if/then/else conditional schema keywords (guards)
            for key, value in resolved_sub.items():
                if key not in ['properties', 'required', 'allOf', '$ref', 'if', 'then', 'else', 
                              'title', 'description', 'version']:
                    if key not in merged:
                        merged[key] = value
        
        # Recursively resolve any $refs in properties
        if 'properties' in merged:
            merged['properties'] = self._resolve_properties(merged['properties'])
        
        return merged
    
    def _resolve_ref(self, ref: str) -> Dict[str, Any]:
        """
        Resolve a $ref to the actual schema.
        
        Supports:
        - URN references: urn:agentic-data-modeler:contract:common:0.3.0#/$defs/envelope
        - Relative references: #/$defs/scalar_value (resolved within current schema context)
        """
        # Handle relative references (starting with #)
        if ref.startswith('#'):
            # Relative ref - resolve within current schema context
            if not self.current_schema_urn:
                raise ValueError(f"Relative $ref '{ref}' encountered without schema context")
            
            # Get the current schema
            schema = self.schemas_cache[self.current_schema_urn]
            
            # Navigate to fragment
            schema = self._navigate_fragment(schema, ref)
            
            # Recursively resolve (keep same context)
            return self.resolve(schema, context_urn=self.current_schema_urn)
        
        # Handle absolute URN references
        if '#' in ref:
            base_urn, fragment = ref.split('#', 1)
        else:
            base_urn = ref
            fragment = None
        
        # Get the schema by URN
        if base_urn not in self.schemas_cache:
            raise ValueError(f"Schema not found for URN: {base_urn}")
        
        schema = self.schemas_cache[base_urn]
        
        # Navigate to fragment if present
        if fragment:
            schema = self._navigate_fragment(schema, fragment)
        
        # Recursively resolve with new context
        return self.resolve(schema, context_urn=base_urn)
    
    def _navigate_fragment(self, schema: Dict[str, Any], fragment: str) -> Dict[str, Any]:
        """
        Navigate to a fragment within a schema.
        
        Example: #/$defs/envelope navigates to schema["$defs"]["envelope"]
        """
        # Remove leading # and /
        if fragment.startswith('#/'):
            fragment = fragment[2:]
        elif fragment.startswith('/'):
            fragment = fragment[1:]
        
        # Split path and navigate
        parts = fragment.split('/')
        current = schema
        
        for part in parts:
            if part not in current:
                raise ValueError(f"Fragment path not found: {fragment} (missing: {part})")
            current = current[part]
        
        return current
    
    def get_table_metadata(self, schema: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract table metadata from a resolved schema.
        
        If title/description/version are not directly in the schema, 
        attempts to extract from $id URN.
        
        Returns:
            Dict with title, description, version
        """
        title = schema.get('title')
        description = schema.get('description', '')
        version = schema.get('version')
        
        # If metadata is missing, try to extract from $id
        if not title or not version:
            schema_id = schema.get('$id', '')
            if schema_id:
                # Parse URN: urn:agentic-data-modeler:contract:<table_name>:<version>
                parts = schema_id.split(':')
                if len(parts) >= 5:
                    if not title:
                        title = parts[-2]  # table_name is second to last
                    if not version:
                        version = parts[-1]  # version is last
        
        return {
            'title': title or 'unknown_table',
            'description': description,
            'version': version or 'unknown'
        }
