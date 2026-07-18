import pytest

from agentic_data_modeler.control import (
    RegistrationError,
    RegistrationParameters,
    registration_rerun_preserves_state,
)


def _valid_parameters() -> dict[str, str]:
    return {
        "registration_mode": "SYNTHETIC_DEV",
        "client_name": "SYNTHETIC_CLIENT_CA_AUTO",
        "authorization_ref": "SYNTHETIC-D23-02-E123-v1",
        "effective_start_date": "2026-07-18",
        "workspace_host": "https://dbc-b2d72a44-d1b1.cloud.databricks.com",
        "execution_principal": "cleancoding109@gmail.com",
        "source_access_granted": "true",
    }


def test_synthetic_registration_parameters_are_explicit() -> None:
    registration = RegistrationParameters.from_parameters(_valid_parameters())
    assert registration.mode.value == "SYNTHETIC_DEV"
    assert registration.source_access_granted is True
    assert registration.note.startswith("SYNTHETIC DEV-ONLY")


@pytest.mark.parametrize(
    ("name", "value", "message"),
    [
        ("registration_mode", "PRODUCTION", "must be SYNTHETIC_DEV"),
        ("client_name", "Real Client", "must start with SYNTHETIC_"),
        ("authorization_ref", "D23-02", "must start with SYNTHETIC-"),
        ("effective_start_date", "18-07-2026", "YYYY-MM-DD"),
        ("workspace_host", "http://example.com", "HTTPS origin"),
        ("workspace_host", "https://example.com/path", "without a path"),
        ("source_access_granted", "false", "explicitly true"),
    ],
)
def test_registration_parameters_fail_closed(name: str, value: str, message: str) -> None:
    parameters = _valid_parameters()
    parameters[name] = value
    with pytest.raises(RegistrationError, match=message):
        RegistrationParameters.from_parameters(parameters)


@pytest.mark.parametrize(
    "workflow_state",
    [
        "VALIDATED",
        "METADATA_READY",
        "PROFILE_READY",
        "EVIDENCE_READY",
        "CONTEXT_READY",
        "SDD_READY",
        "SILVER_READY",
        "GOLD_READY",
        "STTM_READY",
        "PUBLISHED",
    ],
)
def test_registration_rerun_preserves_governed_progress(workflow_state: str) -> None:
    assert registration_rerun_preserves_state(workflow_state)


@pytest.mark.parametrize("workflow_state", ["", "REGISTERED", "FAILED", "UNKNOWN"])
def test_registration_rerun_rejects_unknown_or_regressive_state(
    workflow_state: str,
) -> None:
    assert not registration_rerun_preserves_state(workflow_state)
