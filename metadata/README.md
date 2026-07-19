# Metadata Configuration Rules

## Overview
This directory contains grouped, non-secret job parameters for the Agentic Data Modeler. These parameters enable **Requirements Charter compliance** for reproducibility, governance, and execution control.

## Files
* **`common.json`**: Shared default parameters for all executions
* **`sdd_param.json`**: Deployment-specific overrides that win over common.json

## Parameter Groups

### Core Groups (always required)
* **scope**: Discovery boundary (LOB, domain, table patterns)
* **source**: Source system identity (catalog, schema, system_id)
* **output**: Result locations (control schema, deliverable schemas, Excel volume)
* **knowledge_pack**: Governed input versioning (pack_id, version, approval status)
* **profiling**: Data profiling governance (policy, run_mode, sampling)
* **contracts**: Schema version (must match deployed DDL)

### Governance & Control Groups (Charter §6 compliance)
* **versioning**: Reproducibility versions (config, skill, prompt)
* **governance**: Approval controls (reviewer/approver groups, requirements)
* **execution**: LLM execution limits (temperature, tokens, timeout, cost)

### Deployment-Specific Groups (sdd_param.json overrides)
* **models**: AI model endpoints (producer, critic)
* **identity**: Authorization boundary (workspace, principal, access grant)

## Merge Behavior
The config loader performs a deep merge where:
* `common.json` provides the base defaults
* `sdd_param.json` overrides specific values
* Override wins at every level of nesting
* `_comment` fields are stripped from the final result

## Charter Alignment

This parameter structure directly supports Requirements Charter mandates:

| Charter Requirement | Parameter Group | Keys |
|---------------------|-----------------|------|
| §3: LOB/domain per execution slice | scope | lob, domain |
| §4: Versioned knowledge packs | knowledge_pack | pack_id, pack_version |
| §5: Multiple deliverable types | output | sdd/silver/gold/sttm_schema |
| §5: Excel export location | output | excel_export_volume |
| §6: LLM for semantic analysis | models | producer/critic_endpoint |
| §6: Prevent auto-approval | governance | require_approval_for |
| §6: Authorization boundaries | identity | workspace_host, execution_principal |
| §6: Reproducibility | versioning | config/skill/prompt_version |
| §6: Cost/latency limits | execution | cost_limit, timeout |

## What Goes Here
* **YES**: Static, grouped configuration for scope, source, output, knowledge, profiling, models, identity, contracts, versioning, governance, execution
* **NO**: Secrets (use Databricks secrets)
* **NO**: Dynamic runtime values (run_id, work_package_id, source_tables, snapshot IDs) — these are passed as task values

## Versioning Guidelines

Increment versions when:
* **config_version**: This metadata JSON structure changes materially
* **skill_set_version**: Procedural skills (.md files) are updated
* **prompt_set_version**: System prompts or agent instructions change

Version bumps enable Charter §6 reproducibility: "reproduce outputs from versioned evidence, context, model, prompt, skill, and configuration snapshots."

## Adding Environments
To add another environment (e.g., `prod.json`):
1. Create the new override file following the same structure
2. Override only environment-specific values:
   * `identity`: workspace_host, execution_principal
   * `governance`: reviewer/approver groups for that environment
   * `execution`: cost_limit_per_run_usd (higher for prod)
3. Update the loader to accept the new environment name
4. No changes to existing files needed — the override pattern is extensible

## Security
Never commit secrets, credentials, or sensitive identity information to these files. Use Databricks Secrets for sensitive values.

## Example: Dev vs Prod Overrides

**Dev environment** (`sdd_param.json`):
```json
{
  "execution": {
    "cost_limit_per_run_usd": 50.0
  },
  "governance": {
    "default_approver_group": "dev_approvers"
  }
}
```

**Prod environment** (`prod.json`):
```json
{
  "execution": {
    "cost_limit_per_run_usd": 500.0
  },
  "governance": {
    "default_reviewer_group": "prod_reviewers",
    "default_approver_group": "prod_approvers"
  }
}
```
