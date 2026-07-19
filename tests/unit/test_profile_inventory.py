import pytest

from agentic_data_modeler.evidence import AttributeProfile, ProfileInventory


def _inventory(profiles=None) -> ProfileInventory:
    return ProfileInventory.from_iterable(
        run_id="run-profile-test",
        source_snapshot_id="source_snapshot_1",
        policy_ref="GOV-001@1.0.0:D23-03,D23-04,D23-05",
        template_version="restricted-aggregate/0.1.0",
        profiles=profiles
        or (
            AttributeProfile("pc_policy", "policy_id", 10, 0, 10, "query_1"),
            AttributeProfile("pc_policy", "status", 10, 1, 3, "query_1"),
        ),
    )


def test_profile_inventory_is_stable_and_aggregate_only() -> None:
    forward = _inventory()
    reverse = _inventory(tuple(reversed(forward.profiles)))

    assert forward.fingerprint() == reverse.fingerprint()
    assert forward.snapshot_id() == reverse.snapshot_id()
    assert forward.table_count == 1
    assert forward.attribute_count == 2
    content = forward.profiles[0].content(forward.policy_ref, "2026-08-17")
    assert '"value_retention":"NONE"' in content
    assert '"distinct_method":"EXACT"' in content


@pytest.mark.parametrize(
    "profile",
    [
        AttributeProfile("pc_policy", "status", 10, 11, 3, "query_1"),
        AttributeProfile("pc_policy", "status", 10, 1, 11, "query_1"),
        AttributeProfile("pc_policy", "status", -1, 0, 0, "query_1"),
    ],
)
def test_profile_inventory_rejects_impossible_counts(profile: AttributeProfile) -> None:
    with pytest.raises(ValueError):
        _inventory((profile,))
