import pytest

from agentic_data_modeler.evidence import EvidenceItemReference, EvidenceSetManifest


def _item(record_id: str, seed: str, evidence_type: str = "METADATA"):
    return EvidenceItemReference(record_id, seed * 64, evidence_type)


def _manifest(items):
    return EvidenceSetManifest.from_iterable(
        work_package_id="WP-1234",
        source_snapshot_id="source-1",
        profile_snapshot_id="profile-1",
        document_set_id=None,
        requirement_set_id=None,
        items=items,
    )


def test_manifest_is_order_independent_and_has_stable_ids() -> None:
    first = _manifest([_item("e2", "b", "PROFILE"), _item("e1", "a")])
    second = _manifest([_item("e1", "a"), _item("e2", "b", "PROFILE")])

    assert first.fingerprint() == second.fingerprint()
    assert first.evidence_set_id() == second.evidence_set_id()
    assert first.solution_run_id() == second.solution_run_id()


def test_changed_evidence_changes_fingerprint() -> None:
    assert _manifest([_item("e1", "a")]).fingerprint() != _manifest(
        [_item("e1", "b")]
    ).fingerprint()


@pytest.mark.parametrize(
    "items",
    [[], [_item("e1", "a"), _item("e1", "b")]],
)
def test_empty_or_duplicate_evidence_fails_closed(items) -> None:
    with pytest.raises(ValueError):
        _manifest(items)


def test_invalid_item_fingerprint_fails_closed() -> None:
    with pytest.raises(ValueError, match="SHA-256"):
        _manifest([EvidenceItemReference("e1", "not-a-hash", "METADATA")])
