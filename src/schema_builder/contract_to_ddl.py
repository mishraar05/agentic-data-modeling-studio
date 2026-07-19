"""
Contract to DDL converter.
Reads JSON Schema contracts and generates Delta table DDL.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from .config_loader import ConfigLoader
from .ddl_generator import DDLGenerator


class ContractToDDL:
    """Main class for converting JSON Schema contracts to DDL."""
    
    def __init__(self, config_path: str = "config/env_config.yaml"):
        self.config_loader = ConfigLoader(config_path)
        self.config_loader.load()
        
        # Validate configuration
        errors = self.config_loader.validate()
        if errors:
            print("❌ Configuration validation errors:")
            for error in errors:
                print(f"  - {error}")
            sys.exit(1)
        
        self.ddl_generator = DDLGenerator(self.config_loader)
    
    def process_contracts(self, contracts_dir: str, catalog: str, schema: str,
                         output_dir: str, execute: bool = False) -> Dict[str, Any]:
        contracts_path = Path(contracts_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Find all contract files
        contract_files = [
            path for path in contracts_path.glob("*.schema.json")
            if path.name != "_common.schema.json"
        ]
        
        if not contract_files:
            print(f"⚠️  No *.schema.json files found in {contracts_dir}")
            return {'processed': 0, 'errors': 0}
        
        print(f"📄 Found {len(contract_files)} contract files")
        print(f"🎯 Target: {catalog}.{schema}")
        print(f"📁 Output: {output_dir}")
        print()
        
        processed = 0
        errors = 0
        
        for contract_file in sorted(contract_files):
            try:
                with open(contract_file, 'r', encoding='utf-8') as f:
                    contract = json.load(f)
                
                table_name = contract_file.stem.replace('.schema', '')
                ddl = self.ddl_generator.generate(contract, catalog, schema, table_name)
                
                output_file = output_path / f"{table_name}.sql"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(ddl)
                
                print(f"✅ {table_name:40s} → {output_file.name}")
                
                if execute:
                    self._execute_ddl(ddl)
                
                processed += 1
                
            except Exception as e:
                print(f"❌ {contract_file.name}: {str(e)}")
                errors += 1
        
        print()
        print(f"✅ Processed: {processed}")
        if errors:
            print(f"❌ Errors: {errors}")
        
        return {'processed': processed, 'errors': errors, 'output_dir': str(output_path)}
    
    def _execute_ddl(self, ddl: str):
        pass
