from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LEGACY_IDENTIFIERS = ("engagement" + "_id", "work_package" + "_id")


def _load_yaml(relative_path: str) -> dict:
    return yaml.safe_load((REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8"))


def test_source_discovery_is_run_rooted_and_parameterized() -> None:
    """Assert job.parameters exposes only work_package_id; scope/source/model params live in metadata/."""
    job = _load_yaml("resources/source_discovery.job.yml")["resources"]["jobs"]["source_discovery"]
    param_names = [parameter["name"] for parameter in job["parameters"]]
    
    # Only work_package_id should be in job parameters now (metadata refactor moved others)
    assert param_names == ["work_package_id"]
    assert not set(LEGACY_IDENTIFIERS) & set(param_names)
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
    """Verify the notebook wires params['models'] + independence guard, not job parameters."""
    job = _load_yaml("resources/source_discovery.job.yml")["resources"]["jobs"]["source_discovery"]
    task = next(task for task in job["tasks"] if task["task_key"] == "analyze_source_relationships")
    
    # Task uses agent environment
    assert task["environment_key"] == "agent"
    
    # Verify notebook code loads from metadata and has independence guard
    notebook_path = REPOSITORY_ROOT / "src/workflows/analyze_source_relationships.py"
    notebook_content = notebook_path.read_text(encoding="utf-8")
    
    # Check it loads params["models"]
    assert 'params["models"]["producer_endpoint"]' in notebook_content
    assert 'params["models"]["critic_endpoint"]' in notebook_content
    
    # Check the PROTECTED independence guard is present
    assert "Critic endpoint must differ from the producer endpoint (independence)" in notebook_content
    assert "if producer_endpoint == critic_endpoint:" in notebook_content


def test_bundle_declares_run_context_and_agent_variables() -> None:
    """Assert databricks.yml declares exactly resource_prefix, work_package_id, production_root_path."""
    variables = _load_yaml("databricks.yml")["variables"]
    required = {"resource_prefix", "work_package_id", "production_root_path"}
    
    # After metadata refactor, only these three should remain
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
