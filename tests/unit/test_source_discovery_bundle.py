from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LEGACY_IDENTIFIERS = ("engagement" + "_id", "work_package" + "_id")


def _load_yaml(relative_path: str) -> dict:
    return yaml.safe_load((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))


def test_source_discovery_is_run_rooted_and_parameterized() -> None:
    job = _load_yaml("resources/source_discovery.job.yml")["resources"]["jobs"]["source_discovery"]
    names = [parameter["name"] for parameter in job["parameters"]]

    assert len(names) == len(set(names))
    assert "lob" in names and "domain" in names
    assert "producer_endpoint" in names and "critic_endpoint" in names
    assert not set(LEGACY_IDENTIFIERS) & set(names)
    assert job["max_concurrent_runs"] == 1


def test_job_executes_complete_source_to_relationship_flow() -> None:
    job = _load_yaml("resources/source_discovery.job.yml")["resources"]["jobs"]["source_discovery"]
    tasks = {task["task_key"]: task for task in job["tasks"]}
    assert list(tasks) == [
        "validate_scope",
        "discover_source_scope",
        "register_solution_run",
        "snapshot_source_metadata",
        "profile_source",
        "assemble_source_evidence",
        "assemble_context",
        "analyze_source_relationships",
    ]
    expected_parent = {
        "discover_source_scope": "validate_scope",
        "register_solution_run": "discover_source_scope",
        "snapshot_source_metadata": "register_solution_run",
        "profile_source": "snapshot_source_metadata",
        "assemble_source_evidence": "profile_source",
        "assemble_context": "assemble_source_evidence",
        "analyze_source_relationships": "assemble_context",
    }
    for task_key, parent in expected_parent.items():
        assert tasks[task_key]["depends_on"] == [{"task_key": parent}]


def test_all_source_tasks_share_one_generated_run_identity() -> None:
    job = _load_yaml("resources/source_discovery.job.yml")["resources"]["jobs"]["source_discovery"]
    for task in job["tasks"]:
        parameters = task["notebook_task"]["base_parameters"]
        assert parameters["run_id"] == "source_discovery_{{job.run_id}}"
        assert not set(LEGACY_IDENTIFIERS) & set(parameters)


def test_discovery_freezes_manifest_for_downstream_tasks() -> None:
    job = _load_yaml("resources/source_discovery.job.yml")["resources"]["jobs"]["source_discovery"]
    for task in job["tasks"][2:6]:
        assert task["notebook_task"]["base_parameters"]["source_tables"] == (
            "{{tasks.discover_source_scope.values.source_tables}}"
        )


def test_relationship_agent_has_independent_producer_and_critic() -> None:
    job = _load_yaml("resources/source_discovery.job.yml")["resources"]["jobs"]["source_discovery"]
    task = next(task for task in job["tasks"] if task["task_key"] == "analyze_source_relationships")
    parameters = task["notebook_task"]["base_parameters"]
    assert parameters["producer_endpoint"] == "{{job.parameters.producer_endpoint}}"
    assert parameters["critic_endpoint"] == "{{job.parameters.critic_endpoint}}"
    assert task["environment_key"] == "agent"


def test_bundle_declares_run_context_and_agent_variables() -> None:
    variables = _load_yaml("databricks.yml")["variables"]
    required = {
        "lob", "domain", "source_catalog", "source_schema", "source_tables_json",
        "knowledge_pack_id", "knowledge_pack_version", "knowledge_geography",
        "knowledge_domains",
        "relationship_producer_endpoint", "relationship_critic_endpoint",
    }
    assert required <= set(variables)
    assert not set(LEGACY_IDENTIFIERS) & set(variables)


def test_workflow_bootstraps_synced_source_before_package_import() -> None:
    workflow = (REPOSITORY_ROOT / "src/workflows/validate_source_discovery_scope.py").read_text(
        encoding="utf-8"
    )
    assert workflow.index("_add_bundle_source_to_python_path()") < workflow.index(
        "from agentic_data_modeler.control import RuntimeRequest"
    )
    assert 'PurePosixPath("/Workspace")' in workflow
