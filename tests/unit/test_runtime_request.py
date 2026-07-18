import json

import pytest

from agentic_data_modeler.control import (
    APPROVED_CONTRACT_SET_VERSION,
    ProfilingMode,
    RuntimeRequest,
    RuntimeRequestError,
    SourceScopeMode,
)


def _valid_parameters() -> dict[str, str]:
    return {
        "run_id": "source_discovery_101",
        "engagement_id": "eng_ca_personal_auto",
        "work_package_id": "wp_policy_core",
        "lob": "P&C Personal Auto",
        "domain": "Policy",
        "source_catalog": "guidewire_dev",
        "source_schema": "pc_source",
        "source_scope_mode": "EXPLICIT_TABLES",
        "source_table_include_patterns": "[]",
        "source_table_exclude_patterns": "[]",
        "source_object_types": '["TABLE"]',
        "source_tables": json.dumps(["pc_policy", "pc_policyperiod"]),
        "source_system_id": "guidewire_policycenter",
        "source_product": "PolicyCenter",
        "source_module": "Policy",
        "source_version": "10",
        "run_mode": "METADATA_ONLY",
        "profiling_policy_id": "metadata_only_default",
        "profiling_policy_version": "1.0.0",
        "document_set_id": "",
        "requirement_set_id": "",
        "output_catalog": "insurance_source_discovery",
        "output_schema": "control",
        "contract_set_version": APPROVED_CONTRACT_SET_VERSION,
    }


def test_valid_request_is_typed_and_fingerprinted() -> None:
    request = RuntimeRequest.from_parameters(_valid_parameters())
    assert request.profiling_mode is ProfilingMode.METADATA_ONLY
    assert request.source_scope_mode is SourceScopeMode.EXPLICIT_TABLES
    assert request.source_tables == ("pc_policy", "pc_policyperiod")
    assert len(request.fingerprint()) == 64


def test_equivalent_requests_have_identical_fingerprints() -> None:
    first = RuntimeRequest.from_parameters(_valid_parameters())
    equivalent = dict(reversed(list(_valid_parameters().items())))
    equivalent["run_id"] = "source_discovery_202"
    equivalent["source_tables"] = json.dumps(["pc_policyperiod", "pc_policy"])
    second = RuntimeRequest.from_parameters(equivalent)
    assert first.canonical_payload() == second.canonical_payload()
    assert first.fingerprint() == second.fingerprint()


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("engagement_id", "", "engagement_id is required"),
        ("work_package_id", "REQUIRED_WORK_PACKAGE_ID", "unresolved placeholder"),
        ("source_catalog", "catalog-name", "safe unqualified identifier"),
        ("profiling_policy_version", "latest", "semantic version"),
        ("contract_set_version", "latest", "exactly match"),
    ],
)
def test_invalid_required_boundaries_fail_closed(name: str, value: str, message: str) -> None:
    parameters = _valid_parameters()
    parameters[name] = value
    with pytest.raises(RuntimeRequestError, match=message):
        RuntimeRequest.from_parameters(parameters)


@pytest.mark.parametrize(
    "source_tables",
    [
        "pc_policy,pc_policyperiod",
        "{}",
        "[]",
        '["pc_policy", "pc_policy"]',
        '["pc_policy", "other.table"]',
        '["pc_policy", 7]',
    ],
)
def test_malformed_duplicate_or_unsafe_allow_list_fails(source_tables: str) -> None:
    parameters = _valid_parameters()
    parameters["source_tables"] = source_tables
    with pytest.raises(RuntimeRequestError):
        RuntimeRequest.from_parameters(parameters)


def test_source_and_output_schema_must_be_distinct_case_insensitively() -> None:
    parameters = _valid_parameters()
    parameters["output_catalog"] = "GUIDEWIRE_DEV"
    parameters["output_schema"] = "PC_SOURCE"
    with pytest.raises(RuntimeRequestError, match="must be distinct"):
        RuntimeRequest.from_parameters(parameters)


def test_schema_all_scope_accepts_empty_explicit_table_input() -> None:
    parameters = _valid_parameters()
    parameters["source_scope_mode"] = "SCHEMA_ALL_TABLES"
    parameters["source_table_include_patterns"] = '["*"]'
    parameters["source_table_exclude_patterns"] = '["*_backup"]'
    parameters["source_tables"] = "[]"
    request = RuntimeRequest.from_parameters(parameters)
    assert request.source_tables == ()
    assert request.source_table_include_patterns == ("*",)


def test_explicit_scope_rejects_pattern_configuration() -> None:
    parameters = _valid_parameters()
    parameters["source_table_include_patterns"] = '["pc_*"]'
    with pytest.raises(RuntimeRequestError, match="does not accept"):
        RuntimeRequest.from_parameters(parameters)


def test_unapproved_profiling_mode_fails_closed() -> None:
    parameters = _valid_parameters()
    parameters["run_mode"] = "BOUNDED_DISTRIBUTION"
    with pytest.raises(RuntimeRequestError, match="run_mode must be one of"):
        RuntimeRequest.from_parameters(parameters)


def test_control_characters_are_rejected_before_logging() -> None:
    parameters = _valid_parameters()
    parameters["domain"] = "Policy\nSECRET=value"
    with pytest.raises(RuntimeRequestError, match="prohibited control character"):
        RuntimeRequest.from_parameters(parameters)
