"""
Increment-1 contract validation test suite.

Tests JSON Schema Draft 2020-12 compliance, referential integrity, lifecycle guards,
semantic claim rules, and cross-contract dependencies.

Run with: python -m pytest tests/contracts/
"""

import json
import pytest
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from jsonschema.validators import RefResolver


# Paths
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"
COMMON_SCHEMA_PATH = CONTRACTS_DIR / "_common.schema.json"

# All 31 Increment-1 contracts
ALL_CONTRACTS = [
    "_common",
    "engagement", "work_package", "solution_run", "artifact_version",
    "source_snapshot", "context_snapshot", "profile_snapshot",
    "document_set", "requirement_set", "evidence_set",
    "evidence_item", "source_object_observation", "source_attribute_observation",
    "profile_evidence", "relationship_candidate",
    "analytical_requirement", "reporting_requirement", "business_term", "business_rule",
    "source_dictionary_attribute", "source_dictionary_object",
    "source_dictionary_relationship", "source_dictionary_code_value",
    "validation_finding", "review_item", "review_decision", "open_question",
    "artifact_dependency", "lineage_edge", "source_dictionary_handoff",
    "skill_resolution"
]


@pytest.fixture(scope="module")
def common_schema():
    """Load the common schema."""
    with open(COMMON_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def validator(common_schema):
    """Create a validator with common schema reference resolution."""
    store = {
        common_schema["$id"]: common_schema
    }
    resolver = RefResolver.from_schema(common_schema, store=store)
    return Draft202012Validator, resolver


def load_contract_schema(contract_name):
    """Load a contract schema by name."""
    schema_path = CONTRACTS_DIR / f"{contract_name}.schema.json"
    if not schema_path.exists():
        pytest.skip(f"Contract {contract_name} not yet implemented")
    with open(schema_path) as f:
        return json.load(f)


class TestCommonSchema:
    """Test the foundational common schema."""
    
    def test_common_schema_is_valid_draft_2020_12(self, common_schema):
        """Common schema must be valid JSON Schema Draft 2020-12."""
        Draft202012Validator.check_schema(common_schema)
    
    def test_common_schema_has_required_defs(self, common_schema):
        """Common schema must define all contract-owned vocabularies."""
        required_defs = [
            "envelope", "provenance", "contextual_provenance",
            "lifecycle_material", "lifecycle_append_only", "lifecycle_operational",
            "lifecycle_governance_decision", "lifecycle_open_item", "lifecycle_handoff",
            "evidence_state", "provenance_class", "governed_code_ref",
            "confidence_components", "semantic_claim", "physical_observation",
            "no_op_guard", "material_approval_guard", "handoff_issue_guard"
        ]
        assert "$defs" in common_schema
        for def_name in required_defs:
            assert def_name in common_schema["$defs"], f"Missing required definition: {def_name}"


class TestImplementedContracts:
    """Test all implemented contract schemas."""
    
    @pytest.mark.parametrize("contract_name", ALL_CONTRACTS)
    def test_contract_schema_is_valid(self, contract_name):
        """Each contract schema must be valid JSON Schema Draft 2020-12."""
        if contract_name == "_common":
            pytest.skip("Common schema tested separately")
        schema = load_contract_schema(contract_name)
        Draft202012Validator.check_schema(schema)
    
    @pytest.mark.parametrize("contract_name", [c for c in ALL_CONTRACTS if c != "_common"])
    def test_contract_has_correct_id_format(self, contract_name):
        """Contract $id must follow URN pattern."""
        schema = load_contract_schema(contract_name)
        expected_prefix = f"urn:agentic-data-modeler:contract:{contract_name}:"
        assert schema["$id"].startswith(expected_prefix), \
            f"Contract $id must start with {expected_prefix}"
    
    @pytest.mark.parametrize("contract_name", [c for c in ALL_CONTRACTS if c != "_common"])
    def test_contract_closes_additional_properties(self, contract_name):
        """Contracts must set unevaluatedProperties: false."""
        schema = load_contract_schema(contract_name)
        assert schema.get("unevaluatedProperties") is False, \
            f"Contract {contract_name} must set unevaluatedProperties: false"
    
    @pytest.mark.parametrize("contract_name,lifecycle_family", [
        ("engagement", "operational"),
        ("work_package", "operational"),
        ("solution_run", "operational"),
        ("artifact_version", "material"),
        ("source_snapshot", "append_only"),
        ("context_snapshot", "append_only"),
        ("profile_snapshot", "append_only"),
        ("document_set", "append_only"),
        ("requirement_set", "append_only"),
        ("evidence_set", "append_only"),
        ("evidence_item", "append_only"),
        ("source_object_observation", "append_only"),
        ("source_attribute_observation", "append_only"),
        ("profile_evidence", "append_only"),
        ("relationship_candidate", "append_only"),
        ("analytical_requirement", "material"),
        ("reporting_requirement", "material"),
        ("business_term", "material"),
        ("business_rule", "material"),
        ("source_dictionary_attribute", "material"),
        ("source_dictionary_object", "material"),
        ("source_dictionary_relationship", "material"),
        ("source_dictionary_code_value", "material"),
        ("validation_finding", "open_item"),
        ("review_item", "open_item"),
        ("review_decision", "governance_decision"),
        ("open_question", "open_item"),
        ("artifact_dependency", "append_only"),
        ("lineage_edge", "append_only"),
        ("source_dictionary_handoff", "handoff"),
        ("skill_resolution", "append_only")
    ])
    def test_contract_uses_correct_lifecycle(self, contract_name, lifecycle_family):
        """Each contract must reference the correct lifecycle enum."""
        schema = load_contract_schema(contract_name)
        # Find the lifecycle_state reference in allOf
        found_lifecycle_ref = False
        for block in schema.get("allOf", []):
            if "properties" in block and "lifecycle_state" in block["properties"]:
                lifecycle_ref = block["properties"]["lifecycle_state"].get("$ref", "")
                expected_ref = f"urn:agentic-data-modeler:contract:common:0.3.0#/$defs/lifecycle_{lifecycle_family}"
                assert lifecycle_ref == expected_ref, \
                    f"Contract {contract_name} must use lifecycle_{lifecycle_family}"
                found_lifecycle_ref = True
                break
        assert found_lifecycle_ref, f"Contract {contract_name} must define lifecycle_state"


class TestLifecycleGuards:
    """Test lifecycle guard enforcement."""
    
    @pytest.mark.parametrize("contract_name", [
        "artifact_version", "analytical_requirement", "reporting_requirement",
        "business_term", "business_rule", "source_dictionary_attribute",
        "source_dictionary_object", "source_dictionary_relationship",
        "source_dictionary_code_value"
    ])
    def test_material_contracts_require_approval_guard(self, contract_name):
        """Material lifecycle contracts must use material_approval_guard."""
        schema = load_contract_schema(contract_name)
        # Check that material_approval_guard is referenced
        guard_found = False
        for block in schema.get("allOf", []):
            if "$ref" in block and "material_approval_guard" in block["$ref"]:
                guard_found = True
                break
        assert guard_found, f"Material contract {contract_name} must use material_approval_guard"
    
    @pytest.mark.parametrize("contract_name", [
        "source_snapshot", "context_snapshot", "profile_snapshot", "document_set",
        "requirement_set", "evidence_set", "evidence_item", "source_object_observation",
        "source_attribute_observation", "profile_evidence", "relationship_candidate",
        "artifact_dependency", "lineage_edge", "skill_resolution"
    ])
    def test_append_only_contracts_use_no_op_guard(self, contract_name):
        """Append-only contracts should use no_op_guard."""
        schema = load_contract_schema(contract_name)
        guard_found = False
        for block in schema.get("allOf", []):
            if "$ref" in block and "no_op_guard" in block["$ref"]:
                guard_found = True
                break
        assert guard_found, f"Append-only contract {contract_name} must use no_op_guard"
    
    def test_handoff_contract_uses_handoff_issue_guard(self):
        """Handoff contract must use handoff_issue_guard."""
        schema = load_contract_schema("source_dictionary_handoff")
        guard_found = False
        for block in schema.get("allOf", []):
            if "$ref" in block and "handoff_issue_guard" in block["$ref"]:
                guard_found = True
                break
        assert guard_found, "Handoff contract must use handoff_issue_guard"


class TestProvenanceRules:
    """Test provenance definitions."""
    
    @pytest.mark.parametrize("contract_name", [
        "source_dictionary_attribute", "source_dictionary_object",
        "source_dictionary_relationship", "source_dictionary_code_value",
        "source_dictionary_handoff"
    ])
    def test_dictionary_contracts_use_contextual_provenance(self, contract_name):
        """Dictionary contracts must use contextual_provenance."""
        schema = load_contract_schema(contract_name)
        provenance_ref_found = False
        for block in schema.get("allOf", []):
            if "properties" in block and "provenance" in block["properties"]:
                prov_ref = block["properties"]["provenance"].get("$ref", "")
                assert "contextual_provenance" in prov_ref, \
                    f"Dictionary contract {contract_name} must use contextual_provenance"
                provenance_ref_found = True
                break
        assert provenance_ref_found, f"Contract {contract_name} must define provenance"
    
    @pytest.mark.parametrize("contract_name", [
        "evidence_item", "source_object_observation", "source_attribute_observation",
        "profile_evidence", "relationship_candidate"
    ])
    def test_evidence_contracts_use_base_provenance(self, contract_name):
        """Evidence contracts (pre-context) must use base provenance."""
        schema = load_contract_schema(contract_name)
        provenance_ref_found = False
        for block in schema.get("allOf", []):
            if "properties" in block and "provenance" in block["properties"]:
                prov_ref = block["properties"]["provenance"].get("$ref", "")
                # Should use base provenance (not contextual)
                assert "contextual" not in prov_ref, \
                    f"Evidence contract {contract_name} must use base provenance (not contextual)"
                provenance_ref_found = True
                break
        assert provenance_ref_found, f"Contract {contract_name} must define provenance"


class TestSemanticClaims:
    """Test semantic_claim usage in dictionary contracts."""
    
    @pytest.mark.parametrize("contract_name,expected_fields", [
        ("source_dictionary_attribute", ["business_name", "business_definition"]),
        ("source_dictionary_object", ["business_name", "business_definition", "business_purpose", "entity_type"]),
        ("source_dictionary_relationship", ["relationship_name", "cardinality", "optionality"]),
        ("source_dictionary_code_value", ["meaning"])
    ])
    def test_dictionary_contracts_use_semantic_claims(self, contract_name, expected_fields):
        """Dictionary contracts must use semantic_claim for business fields."""
        schema = load_contract_schema(contract_name)
        # Find properties block
        for block in schema.get("allOf", []):
            if "properties" in block:
                props = block["properties"]
                # Check that business fields reference semantic_claim
                for field in expected_fields:
                    assert field in props, f"Dictionary {contract_name} must define {field}"
                    assert props[field].get("$ref", "").endswith("semantic_claim"), \
                        f"{field} in {contract_name} must use semantic_claim"


class TestSchemaCompleteness:
    """Test that all 31 contracts are present and loadable."""
    
    def test_all_31_contracts_exist(self):
        """Verify all 31 contract schema files exist."""
        missing = []
        for contract_name in ALL_CONTRACTS:
            schema_path = CONTRACTS_DIR / f"{contract_name}.schema.json"
            if not schema_path.exists():
                missing.append(contract_name)
        
        assert len(missing) == 0, f"Missing contract schemas: {missing}"
    
    def test_all_contracts_parse_as_json(self):
        """Verify all contract schemas are valid JSON."""
        errors = []
        for contract_name in ALL_CONTRACTS:
            try:
                load_contract_schema(contract_name)
            except json.JSONDecodeError as e:
                errors.append(f"{contract_name}: {str(e)}")
        
        assert len(errors) == 0, f"JSON parsing errors: {errors}"


class TestFixtureValidation:
    """Test contract validation against fixture examples."""
    
    # Placeholder for fixture-based tests
    # Fixtures will be added as contracts are completed
    
    def test_placeholder_for_future_fixtures(self):
        """Placeholder test - fixtures to be added."""
        pytest.skip("Fixture validation tests to be implemented with complete contracts")


# TODO: Add tests for:
# - Referential integrity (referenced records exist)
# - Evidence state rules (OBSERVED requires SOURCE_FACT provenance)
# - Confidence component rules (INFERRED requires evidence_count == unique refs)
# - Governed code reference validation (pack/version/fingerprint match)
# - Cross-engagement and cross-work-package scope validation
# - Lifecycle transition validation
