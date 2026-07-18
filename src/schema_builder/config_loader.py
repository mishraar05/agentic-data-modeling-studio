"""
Configuration loader for schema builder.
Loads and validates env_config.yaml.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional


class ConfigLoader:
    """Load and validate environment configuration."""
    
    def __init__(self, config_path: str = "config/env_config.yaml"):
        self.config_path = Path(config_path)
        self.config = None
        
    def load(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        return self.config
    
    def validate(self) -> List[str]:
        """Validate configuration structure and values."""
        if self.config is None:
            self.load()
        
        errors = []
        
        # Check required top-level keys
        required_keys = ['catalog', 'guidewire_products', 'layers', 
                         'control_schema', 'schema_naming', 'proof_slice']
        for key in required_keys:
            if key not in self.config:
                errors.append(f"Missing required key: {key}")
        
        # Validate proof slice references
        if 'proof_slice' in self.config:
            proof = self.config['proof_slice']
            
            # Check product exists
            valid_products = [p['code'] for p in self.config.get('guidewire_products', [])]
            if proof.get('product') not in valid_products:
                errors.append(f"Proof slice product '{proof.get('product')}' not in guidewire_products")
            
            # Check layer exists
            if proof.get('layer') not in self.config.get('layers', {}):
                errors.append(f"Proof slice layer '{proof.get('layer')}' not in layers")
        
        # Check schema naming pattern
        if 'schema_naming' in self.config:
            pattern = self.config['schema_naming'].get('pattern', '')
            if '{product_code}' not in pattern or '{layer_suffix}' not in pattern:
                errors.append("Schema naming pattern must include {product_code} and {layer_suffix}")
        
        return errors
    
    def get_schema_name(self, product_code: str, layer: str) -> str:
        """Generate schema name from product and layer."""
        if self.config is None:
            self.load()
        
        layer_suffix = self.config['layers'][layer]['suffix']
        pattern = self.config['schema_naming']['pattern']
        
        return pattern.format(product_code=product_code, layer_suffix=layer_suffix)
    
    def get_enabled_schemas(self) -> List[Dict[str, str]]:
        """Get schemas that are enabled for DDL generation."""
        if self.config is None:
            self.load()
        
        enabled = []
        
        for gen_config in self.config['schema_builder']['generate_for']:
            if gen_config.get('enabled', False):
                product = gen_config['product']
                layer = gen_config['layer']
                schema_name = self.get_schema_name(product, layer)
                
                enabled.append({
                    'schema': schema_name,
                    'product': product,
                    'layer': layer,
                    'catalog': self.config['catalog']['name'],
                    'output_dir': f"{self.config['schema_builder']['output_base_dir']}{schema_name}/"
                })
        
        return enabled
    
    def get_catalog_name(self) -> str:
        """Get catalog name from config."""
        if self.config is None:
            self.load()
        return self.config['catalog']['name']
    
    def get_contracts_dir(self) -> str:
        """Get contracts directory from config."""
        if self.config is None:
            self.load()
        return self.config['schema_builder']['contracts_dir']
