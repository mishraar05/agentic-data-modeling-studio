"""Deterministic aggregate-profile evidence model."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .metadata import stable_record_id


@dataclass(frozen=True, order=True)
class AttributeProfile:
    object_name: str
    attribute_name: str
    row_count: int
    null_count: int
    distinct_count: int
    query_ref: str

    def validate(self) -> None:
        if not self.object_name or not self.attribute_name or not self.query_ref:
            raise ValueError("profile identity and query reference are required")
        if min(self.row_count, self.null_count, self.distinct_count) < 0:
            raise ValueError("profile counts cannot be negative")
        if self.null_count > self.row_count:
            raise ValueError("null count cannot exceed row count")
        if self.distinct_count > self.row_count:
            raise ValueError("distinct count cannot exceed row count")

    def content(self, policy_ref: str, retention_until: str) -> str:
        self.validate()
        return json.dumps(
            {
                "attribute_name": self.attribute_name,
                "distinct_count": self.distinct_count,
                "distinct_method": "EXACT",
                "null_count": self.null_count,
                "object_name": self.object_name,
                "policy_ref": policy_ref,
                "query_ref": self.query_ref,
                "retention_until": retention_until,
                "row_count": self.row_count,
                "value_retention": "NONE",
            },
            sort_keys=True,
            separators=(",", ":"),
        )


@dataclass(frozen=True)
class ProfileInventory:
    work_package_id: str
    source_snapshot_id: str
    policy_ref: str
    template_version: str
    profiles: tuple[AttributeProfile, ...]

    @classmethod
    def from_iterable(
        cls,
        *,
        work_package_id: str,
        source_snapshot_id: str,
        policy_ref: str,
        template_version: str,
        profiles,
    ) -> "ProfileInventory":
        inventory = cls(
            work_package_id=work_package_id,
            source_snapshot_id=source_snapshot_id,
            policy_ref=policy_ref,
            template_version=template_version,
            profiles=tuple(sorted(profiles)),
        )
        inventory.validate()
        return inventory

    @property
    def table_count(self) -> int:
        return len({profile.object_name for profile in self.profiles})

    @property
    def attribute_count(self) -> int:
        return len(self.profiles)

    def validate(self) -> None:
        if not all(
            (self.work_package_id, self.source_snapshot_id, self.policy_ref, self.template_version)
        ):
            raise ValueError("profile inventory identity is required")
        if not self.profiles:
            raise ValueError("profile inventory cannot be empty")
        identities = set()
        for profile in self.profiles:
            profile.validate()
            identity = (profile.object_name, profile.attribute_name)
            if identity in identities:
                raise ValueError(f"duplicate attribute profile: {identity}")
            identities.add(identity)

    def canonical_payload(self) -> dict:
        self.validate()
        return {
            "policy_ref": self.policy_ref,
            "profiles": [
                {
                    "attribute": profile.attribute_name,
                    "distinct_count": profile.distinct_count,
                    "null_count": profile.null_count,
                    "object": profile.object_name,
                    "query_ref": profile.query_ref,
                    "row_count": profile.row_count,
                }
                for profile in self.profiles
            ],
            "source_snapshot_id": self.source_snapshot_id,
            "template_version": self.template_version,
            "work_package_id": self.work_package_id,
        }

    def fingerprint(self) -> str:
        canonical = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def snapshot_id(self) -> str:
        return stable_record_id("profile_snapshot", self.fingerprint())

    def query_set_ref(self) -> str:
        query_refs = sorted({profile.query_ref for profile in self.profiles})
        return stable_record_id("profile_query_set", *query_refs)
