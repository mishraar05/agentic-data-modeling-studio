"""Validation for dev-only synthetic control-plane registration inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Mapping
from urllib.parse import urlparse


class RegistrationError(ValueError):
    """Raised before control-table writes when registration is unauthorized."""


class RegistrationMode(StrEnum):
    """Explicitly supported registration modes."""

    SYNTHETIC_DEV = "SYNTHETIC_DEV"


def _required(parameters: Mapping[str, Any], name: str) -> str:
    raw = parameters.get(name)
    if not isinstance(raw, str) or not raw.strip():
        raise RegistrationError(f"{name} is required")
    value = raw.strip()
    if value.upper().startswith(("REQUIRED_", "TODO", "TBD")):
        raise RegistrationError(f"{name} contains an unresolved placeholder")
    if any(character in value for character in ("\x00", "\r", "\n")):
        raise RegistrationError(f"{name} contains a prohibited control character")
    return value


@dataclass(frozen=True, slots=True)
class RegistrationParameters:
    """Human-supplied authority needed to register one dev work package."""

    mode: RegistrationMode
    client_name: str
    authorization_ref: str
    effective_start_date: date
    workspace_host: str
    execution_principal: str
    source_access_granted: bool

    @classmethod
    def from_parameters(cls, parameters: Mapping[str, Any]) -> "RegistrationParameters":
        mode_value = _required(parameters, "registration_mode")
        try:
            mode = RegistrationMode(mode_value)
        except ValueError as exc:
            raise RegistrationError("registration_mode must be SYNTHETIC_DEV") from exc

        client_name = _required(parameters, "client_name")
        authorization_ref = _required(parameters, "authorization_ref")
        if not client_name.startswith("SYNTHETIC_"):
            raise RegistrationError("synthetic client_name must start with SYNTHETIC_")
        if not authorization_ref.startswith("SYNTHETIC-"):
            raise RegistrationError("synthetic authorization_ref must start with SYNTHETIC-")

        effective_date_value = _required(parameters, "effective_start_date")
        try:
            effective_start_date = date.fromisoformat(effective_date_value)
        except ValueError as exc:
            raise RegistrationError("effective_start_date must use YYYY-MM-DD") from exc

        workspace_host = _required(parameters, "workspace_host").rstrip("/")
        parsed_host = urlparse(workspace_host)
        if parsed_host.scheme != "https" or not parsed_host.netloc or parsed_host.path:
            raise RegistrationError("workspace_host must be an HTTPS origin without a path")

        access_value = _required(parameters, "source_access_granted").casefold()
        if access_value != "true":
            raise RegistrationError("source_access_granted must be explicitly true")

        return cls(
            mode=mode,
            client_name=client_name,
            authorization_ref=authorization_ref,
            effective_start_date=effective_start_date,
            workspace_host=workspace_host,
            execution_principal=_required(parameters, "execution_principal"),
            source_access_granted=True,
        )

    @property
    def note(self) -> str:
        return "SYNTHETIC DEV-ONLY RECORD; NOT PRODUCTION AUTHORIZATION"
