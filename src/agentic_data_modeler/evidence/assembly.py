"""Deterministic assembly of immutable source evidence sets."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from .metadata import stable_record_id


@dataclass(frozen=True, order=True, slots=True)
class EvidenceItemReference:
    record_id: str
    fingerprint: str
    evidence_type: str

    def validate(self) -> None:
        if not self.record_id or not self.evidence_type:
            raise ValueError("evidence item identity and type are required")
        if len(self.fingerprint) != 64 or any(
            character not in "0123456789abcdef" for character in self.fingerprint
        ):
            raise ValueError("evidence item fingerprint must be lowercase SHA-256")


@dataclass(frozen=True, slots=True)
class EvidenceSetManifest:
    run_id: str
    source_snapshot_id: str
    profile_snapshot_id: str | None
    document_set_id: str | None
    requirement_set_id: str | None
    items: tuple[EvidenceItemReference, ...]
    assembler_version: str = "source-evidence-assembler/0.1.0"

    @classmethod
    def from_iterable(
        cls,
        *,
        run_id: str,
        source_snapshot_id: str,
        profile_snapshot_id: str | None,
        document_set_id: str | None,
        requirement_set_id: str | None,
        items,
    ) -> "EvidenceSetManifest":
        manifest = cls(
            run_id=run_id,
            source_snapshot_id=source_snapshot_id,
            profile_snapshot_id=profile_snapshot_id,
            document_set_id=document_set_id,
            requirement_set_id=requirement_set_id,
            items=tuple(sorted(items)),
        )
        manifest.validate()
        return manifest

    def validate(self) -> None:
        if not self.run_id or not self.source_snapshot_id:
            raise ValueError("solution run and source snapshot are required")
        if not self.items:
            raise ValueError("evidence set cannot be empty")
        identities = set()
        for item in self.items:
            item.validate()
            if item.record_id in identities:
                raise ValueError(f"duplicate evidence item: {item.record_id}")
            identities.add(item.record_id)

    def canonical_payload(self) -> dict:
        self.validate()
        return {
            "assembler_version": self.assembler_version,
            "document_set_id": self.document_set_id,
            "items": [
                {
                    "evidence_type": item.evidence_type,
                    "fingerprint": item.fingerprint,
                    "record_id": item.record_id,
                }
                for item in self.items
            ],
            "profile_snapshot_id": self.profile_snapshot_id,
            "requirement_set_id": self.requirement_set_id,
            "source_snapshot_id": self.source_snapshot_id,
            "run_id": self.run_id,
        }

    def fingerprint(self) -> str:
        canonical = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def evidence_set_id(self) -> str:
        return stable_record_id("evidence_set", self.fingerprint())

    def assembly_run_id(self) -> str:
        return stable_record_id("evidence_assembly_run", self.fingerprint())
