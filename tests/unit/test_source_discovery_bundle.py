from pathlib import Path

import yaml


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_PARAMETER_NAMES = {
    "engagement_id",
    "work_package_id",
    "lob",
    "domain",
    "source_catalog",
    "source_schema",
    "source_tables",
    "source_system_id",
    "source_product",
    "source_module",
    "source_version",
    "run_mode",
    "profiling_policy_id",
    "profiling_policy_version",
    "document_set_id",
    "requirement_set_id",
    "output_catalog",
    "output_schema",
    "contract_set_version",
}
REGISTRATION_PARAMETER_NAMES = {
    "registration_mode",
    "client_name",
    "authorization_ref",
    "effective_start_date",
    "workspace_host",
    "execution_principal",
    "source_access_granted",
}
JOB_PARAMETER_NAMES = RUNTIME_PARAMETER_NAMES | REGISTRATION_PARAMETER_NAMES


def _load_yaml(relative_path: str) -> dict:
    path = REPOSITORY_ROOT / relative_path
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_source_discovery_is_a_separate_parameterized_job() -> None:
    resource = _load_yaml("resources/source_discovery.job.yml")
    job = resource["resources"]["jobs"]["source_discovery"]
    names = [parameter["name"] for parameter in job["parameters"]]

    assert len(names) == len(set(names))
    assert set(names) == JOB_PARAMETER_NAMES
    assert job["max_concurrent_runs"] == 1


def test_validation_task_receives_every_job_parameter_and_generated_run_id() -> None:
    resource = _load_yaml("resources/source_discovery.job.yml")
    job = resource["resources"]["jobs"]["source_discovery"]
    task = job["tasks"][0]
    base_parameters = task["notebook_task"]["base_parameters"]

    assert task["task_key"] == "validate_scope"
    assert task["notebook_task"]["notebook_path"].endswith(
        "src/workflows/validate_source_discovery_scope.py"
    )
    assert set(base_parameters) == RUNTIME_PARAMETER_NAMES | {"run_id"}
    assert base_parameters["run_id"] == "source_discovery_{{job.run_id}}"
    for name in RUNTIME_PARAMETER_NAMES:
        assert base_parameters[name] == f"{{{{job.parameters.{name}}}}}"


def test_registration_task_depends_on_validation_and_receives_all_parameters() -> None:
    resource = _load_yaml("resources/source_discovery.job.yml")
    job = resource["resources"]["jobs"]["source_discovery"]
    task = job["tasks"][1]
    base_parameters = task["notebook_task"]["base_parameters"]

    assert task["task_key"] == "register_work_package"
    assert task["depends_on"] == [{"task_key": "validate_scope"}]
    assert task["notebook_task"]["notebook_path"].endswith(
        "src/workflows/register_work_package.py"
    )
    assert set(base_parameters) == JOB_PARAMETER_NAMES | {"run_id"}
    assert base_parameters["run_id"] == "source_discovery_{{job.run_id}}"
    for name in JOB_PARAMETER_NAMES:
        assert base_parameters[name] == f"{{{{job.parameters.{name}}}}}"


def test_bundle_declares_every_source_discovery_variable_default() -> None:
    bundle = _load_yaml("databricks.yml")
    variables = bundle["variables"]
    required_variable_names = {
        "engagement_id",
        "work_package_id",
        "lob",
        "domain",
        "source_catalog",
        "source_schema",
        "source_tables_json",
        "source_system_id",
        "source_product",
        "source_module",
        "source_version",
        "run_mode",
        "profiling_policy_id",
        "profiling_policy_version",
        "registration_mode",
        "client_name",
        "authorization_ref",
        "effective_start_date",
        "workspace_host",
        "execution_principal",
        "source_access_granted",
        "output_catalog",
        "output_schema",
    }
    assert required_variable_names <= set(variables)


def test_workflow_bootstraps_synced_source_before_package_import() -> None:
    workflow = (
        REPOSITORY_ROOT / "src/workflows/validate_source_discovery_scope.py"
    ).read_text(encoding="utf-8")
    bootstrap_call = workflow.index("_add_bundle_source_to_python_path()")
    package_import = workflow.index("from agentic_data_modeler.control import RuntimeRequest")
    assert bootstrap_call < package_import
    assert 'PurePosixPath("/Workspace")' in workflow
