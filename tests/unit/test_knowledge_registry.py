import hashlib
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

from agentic_data_modeler.knowledge import KnowledgeSelectionError, select_approved_pack
from agentic_data_modeler.knowledge.validation import validate_repository_pack


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PACK_ROOT = REPOSITORY_ROOT / "knowledge/packs/public_us_pnc_personal_auto/0.6.0"
MANIFEST = "knowledge/packs/public_us_pnc_personal_auto/0.6.0/manifest.yml"
JURISDICTION_MODULE = PACK_ROOT / "extensions/jurisdiction/module.yml"
SOURCE_REGISTRY = REPOSITORY_ROOT / "knowledge/sources/public_references_v0.6.0.yml"
HISTORICAL_MANIFEST_HASHES = {
    "0.3.0": "f32192c32057c94e54d292c0c000dfa4a392a227784cb244ae37a0dfd32e0f22",
    "0.4.0": "62a4cb9d08d18b22a6070f5a4015509331f9e2e15ce049cc7995409f9c49922a",
    "0.5.0": "343926d9800c2d15cd3a01f0e2076fb1901cc116aa31f4dd99de40fe0a31c0fa",
}


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_module(relative_path: str) -> dict:
    return _load_yaml(PACK_ROOT / relative_path)


def _known_sources() -> set[str]:
    return {item["source_id"] for item in _load_yaml(SOURCE_REGISTRY)["sources"]}


def test_canonical_approved_pack_is_structurally_valid() -> None:
    manifest = validate_repository_pack(REPOSITORY_ROOT, MANIFEST)
    assert manifest["pack_id"] == "public_us_pnc_personal_auto"
    assert manifest["pack_version"] == "0.6.0"
    assert len(manifest["modules"]) == 16
    assert len(manifest["assets"]) == 10


def test_approved_pack_is_runtime_selectable_by_exact_scope() -> None:
    manifest = select_approved_pack(
        REPOSITORY_ROOT,
        pack_id="public_us_pnc_personal_auto",
        pack_version="0.6.0",
        geography="US_general",
        lob="personal_auto",
        domains={"policy", "claims"},
    )

    assert manifest["approval_state"] == "APPROVED"
    assert manifest["runtime_eligible"] is True
    assert all(
        _load_yaml(REPOSITORY_ROOT / item["path"])["approval_state"] == "APPROVED"
        for item in manifest["modules"]
    )
    assert all(
        _load_yaml(REPOSITORY_ROOT / item["path"])["runtime_eligible"] is True
        for item in manifest["modules"]
    )


def test_missing_version_does_not_fallback() -> None:
    with pytest.raises(KnowledgeSelectionError, match="Exactly one"):
        select_approved_pack(
            REPOSITORY_ROOT,
            pack_id="public_us_pnc_personal_auto",
            pack_version="9.9.9",
            geography="US_general",
            lob="personal_auto",
            domains={"policy"},
        )


def test_manifest_path_cannot_escape_repository() -> None:
    with pytest.raises(Exception, match="escapes repository root"):
        validate_repository_pack(REPOSITORY_ROOT, "../outside.yml")


def test_knowledge_root_exposes_only_canonical_areas() -> None:
    directories = {path.name for path in (REPOSITORY_ROOT / "knowledge").iterdir() if path.is_dir()}
    assert directories == {"archive", "packs", "registry", "schemas", "sources"}


def test_archived_manifest_fingerprints_are_preserved() -> None:
    index = _load_yaml(REPOSITORY_ROOT / "knowledge/archive/archive_index.yml")
    for record in index["preserved_manifests"]:
        path = REPOSITORY_ROOT / record["path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]


def test_prior_canonical_candidates_are_preserved_and_superseded() -> None:
    registry = _load_yaml(REPOSITORY_ROOT / "knowledge/registry/pack_registry.yml")
    for version, expected_hash in HISTORICAL_MANIFEST_HASHES.items():
        entry = next(
            item
            for item in registry["packs"]
            if item["pack_id"] == "public_us_pnc_personal_auto" and item["pack_version"] == version
        )
        assert entry["lifecycle"] == "SUPERSEDED_CANDIDATE"
        assert hashlib.sha256((REPOSITORY_ROOT / entry["manifest"]).read_bytes()).hexdigest() == expected_hash


def test_completeness_score_is_recomputed_from_dimensions() -> None:
    assessment = _load_yaml(PACK_ROOT / "completeness.yml")
    assert sum(item["weight_percent"] for item in assessment["dimensions"]) == 100
    weighted_score = sum(
        item["weight_percent"] * item["coverage_percent"] for item in assessment["dimensions"]
    ) / 100
    assert weighted_score == pytest.approx(74.85)
    assert assessment["content_completeness_percent"] == round(weighted_score) == 75
    expert = next(
        item for item in assessment["dimensions"] if item["dimension"] == "expert_validation_and_evaluation"
    )
    assert expert["coverage_percent"] == 0
    assert assessment["trusted_runtime_readiness_percent"] == 0


def test_business_glossary_is_valid_unique_and_source_resolved() -> None:
    glossary = _load_yaml(PACK_ROOT / "glossary/business_terms.yml")
    schema = json.loads((REPOSITORY_ROOT / "knowledge/schemas/glossary.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(glossary, schema)
    term_ids = [item["term_id"] for item in glossary["terms"]]
    assert len(term_ids) >= 45
    assert len(term_ids) == len(set(term_ids))
    known = _known_sources()
    assert all(set(item["source_references"]) <= known for item in glossary["terms"])


def test_semantic_code_sets_are_valid_and_do_not_collapse_unknown_states() -> None:
    catalog = _load_yaml(PACK_ROOT / "code_sets/personal_auto_semantic_codes.yml")
    schema = json.loads((REPOSITORY_ROOT / "knowledge/schemas/code_set.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(catalog, schema)
    ids = [item["code_set_id"] for item in catalog["code_sets"]]
    assert len(ids) == len(set(ids)) == 10
    known = _known_sources()
    assert all(item["source_reference"] in known for item in catalog["code_sets"])
    unknown_set = next(item for item in catalog["code_sets"] if item["code_set_id"] == "unknown_handling_state")
    assert {item["code"] for item in unknown_set["values"]} == {
        "KNOWN", "MISSING", "UNKNOWN", "INVALID", "NOT_APPLICABLE", "WITHHELD", "UNMAPPED"
    }


def test_party_contract_separates_identity_roles_and_privacy() -> None:
    content = _load_module("insurance_core/party/module.yml")["content"]
    grains = {item["record"] for item in content["identity_and_grain"]}
    assert {"party", "party_identifier", "party_role", "party_relationship"} <= grains
    assert "driver_license_identifier" in content["privacy_and_minimization"]["candidate_pii"]
    assert "No individual signal is a universal match rule." in content["identity_resolution_evidence"]["rules"]


def test_billing_contract_separates_premium_cash_and_reconciliation_bases() -> None:
    content = _load_module("insurance_core/billing/module.yml")["content"]
    bases = {item["basis"] for item in content["premium_and_cash_bases"]}
    assert {"written_premium", "earned_premium", "billed_amount", "cash_received", "allocated_cash"} <= bases
    contracts = {item["contract"] for item in content["reconciliation_contracts"]}
    assert contracts == {"receipt_allocation", "invoice_balance", "policy_billing_premium", "commission"}
    assert "not_written_billed_or_earned" in next(
        item["warning"] for item in content["premium_and_cash_bases"] if item["basis"] == "quoted_premium"
    )


def test_claims_lifecycle_preserves_total_loss_and_recovery_components() -> None:
    content = _load_module("personal_auto/claims_lifecycle/module.yml")["content"]
    total_loss_records = set(content["physical_damage"]["total_loss"]["records"])
    assert {"valuation_version", "comparable_vehicle", "gross_settlement", "salvage_value"} <= total_loss_records
    recovery_records = set(content["recovery_and_subrogation"]["records"])
    assert {"recovery_opportunity", "recovery_transaction", "recovery_expense", "deductible_interest"} <= recovery_records
    assert "Recovery does not erase the original paid-loss transaction." in content["recovery_and_subrogation"]["rules"]


def test_modeling_standards_define_enforceable_contracts() -> None:
    silver = _load_yaml(PACK_ROOT / "standards/silver_modeling.yml")
    gold = _load_yaml(PACK_ROOT / "standards/gold_modeling.yml")
    sttm = _load_yaml(PACK_ROOT / "standards/sttm.yml")
    quality = _load_yaml(PACK_ROOT / "standards/naming_datatypes_quality.yml")
    assert {"source_and_business_keys", "privacy_classification", "unresolved_questions"} <= set(
        silver["required_entity_contract"]
    )
    assert {"transaction", "periodic_snapshot", "accumulating_snapshot", "factless"} == set(gold["fact_types"])
    assert "source_evidence_ids" in sttm["required_mapping_fields"]["source"]
    assert "reconciliation_rules" in sttm["required_mapping_fields"]["quality"]
    assert quality["severity_policy"]["critical"].startswith("security_privacy")


def test_fibo_reference_is_pinned_but_concepts_remain_unapproved() -> None:
    fibo = _load_yaml(PACK_ROOT / "references/ontology/fibo.yml")
    assert fibo["pinned_release"]["git_tag"] == "master_2026Q1"
    assert fibo["pinned_release"]["commit_short"] == "574a831"
    assert fibo["concept_selection_status"] == "NOT_APPROVED"
    assert fibo["ontology_creation_deliverable"] is False


def test_policy_semantic_spine_declares_natural_grains_and_timelines() -> None:
    content = _load_module("insurance_core/policy/module.yml")["content"]
    grains = {item["record"] for item in content["identity_and_grain"]}
    assert {"policy", "policy_term", "policy_version", "policy_transaction", "policy_risk_coverage"} <= grains
    axes = {item["axis"] for item in content["timeline_axes"]}
    assert axes == {"contract_effective_time", "transaction_time", "accounting_time", "source_capture_time"}


def test_claim_operational_identity_is_not_replaced_by_regulatory_counting_grain() -> None:
    content = _load_module("insurance_core/claims/module.yml")["content"]
    context = content["regulator_aligned_counting_context"]
    assert context["claim_count_grain"] == "claimant_or_insured_by_coverage_part"
    assert "does not redefine operational claim identity" in context["warning"]


def test_vehicle_enrichment_preserves_observed_source_values() -> None:
    governance = _load_module("personal_auto/risk_and_vehicle/module.yml")["content"]["vin_governance"]
    assert governance["standard_vin_length"] == 17
    serialized = yaml.safe_dump(governance["enrichment_rules"])
    assert "Preserve the raw source VIN" in serialized
    assert "do not overwrite conflicting source facts silently" in serialized


def test_kpi_contract_preserves_formula_context_and_unresolved_financial_definitions() -> None:
    content = _load_module("personal_auto/kpis/module.yml")["content"]
    kpis = {item["kpi_id"]: item for item in content["regulator_aligned_kpis"]}
    assert kpis["claims_closed_without_payment_ratio"]["denominator"] == (
        "claims_closed_with_payment + claims_closed_without_payment"
    )
    assert kpis["median_days_to_final_payment"]["statistic"] == "median"
    unresolved = {item["kpi_id"] for item in content["unresolved_enterprise_kpis"]}
    assert {"earned_premium", "incurred_loss", "loss_ratio", "combined_ratio"} <= unresolved


def test_public_naic_references_retain_licensing_review_gate() -> None:
    sources = {item["source_id"]: item for item in _load_yaml(SOURCE_REGISTRY)["sources"]}
    for source_id in ("naic_mcas_ppa_2026", "naic_mcas_ratios_2026"):
        assert sources[source_id]["usage_basis"].endswith("pending_licensing_review")


def test_california_personal_auto_notice_rules_use_chapter_10() -> None:
    rules = _load_yaml(JURISDICTION_MODULE)["content"]["california"]["cancellation_and_nonrenewal"]
    by_action = {item["action"]: item for item in rules["notice_rules"]}
    assert by_action["cancellation_other_than_nonpayment"]["minimum_notice_days"] == 20
    assert by_action["cancellation_for_nonpayment"]["minimum_notice_days"] == 10
    assert by_action["nonrenewal"]["minimum_notice_days"] == 30
    assert by_action["renewal_offer"]["minimum_notice_days"] == 20
    serialized = yaml.safe_dump(rules)
    assert "ca_ins_code_677_2" not in serialized
    assert "ca_ins_code_678_1" not in serialized


def test_financial_responsibility_is_not_reduced_to_compulsory_coverage() -> None:
    california = _load_yaml(JURISDICTION_MODULE)["content"]["california"]
    responsibility = california["financial_responsibility"]
    assert responsibility["required"] is True
    assert set(responsibility["acceptable_mechanisms"]) == {
        "motor_vehicle_liability_insurance_policy",
        "cash_deposit_with_dmv",
        "dmv_issued_self_insurance_certificate",
        "surety_bond_from_licensed_company",
    }


def test_claim_timing_exceptions_and_fraud_alternatives_are_preserved() -> None:
    obligations = _load_yaml(JURISDICTION_MODULE)["content"]["california"]["claim_obligations"]
    by_name = {item["obligation"]: item for item in obligations}
    assert "automobile_repair_bills" in by_name["accept_or_deny_claim"]["exception"]
    assert by_name["suspected_fraud_decision_period"]["alternatives"] == [
        "increased_to_80_calendar_days",
        "suspended_until_otherwise_ordered_by_insurance_commissioner",
    ]


def test_california_regulations_use_official_primary_sources() -> None:
    sources = {item["source_id"]: item for item in _load_yaml(SOURCE_REGISTRY)["sources"]}
    for source_id in ("ca_ccr_2695_5", "ca_ccr_2695_7", "ca_ccr_2695_8"):
        source = sources[source_id]
        assert source["publisher"] == "Barclays Official California Code of Regulations"
        assert source["url"].startswith("https://govt.westlaw.com/calregs/")
