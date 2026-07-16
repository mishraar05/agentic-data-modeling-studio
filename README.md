# Agentic Data Modeling Studio

A Databricks Declarative Automation Bundle for an Agentic Data Analyst and Modeler that creates a reconstructed Source Data Dictionary, Silver ODS model, Gold dimensional model, and source-to-target mappings for a selected LOB and domain.

## Controlling documents

1. [`docs/requirements/REQUIREMENTS_CHARTER.md`](docs/requirements/REQUIREMENTS_CHARTER.md)
2. [`docs/architecture/AGENT_SOLUTION_ARCHITECTURE.md`](docs/architecture/AGENT_SOLUTION_ARCHITECTURE.md)
3. [`AGENTS.md`](AGENTS.md)

Requirements take precedence over architecture, and architecture takes precedence over implementation plans.

## Bundle layout

| Path | Purpose |
|---|---|
| `databricks.yml` | Bundle identity, variables, sync rules, and deployment targets |
| `resources/` | Databricks jobs and app resource definitions |
| `src/agentic_data_modeler/` | Reusable agent harness and domain-independent Python code |
| `src/workflows/` | Thin Databricks workflow entry points |
| `src/apps/model_review/` | Streamlit review application |
| `contracts/` | Versioned structured artifact contracts |
| `prompts/` | Versioned system and task prompts |
| `skills/` | Runtime `SKILL.md` packages used by the agent harness |
| `evals/` | Golden sets, scorers, adversarial cases, and evaluation configuration |
| `knowledge/` | Versioned, authorized ontology, glossary, standards, LOB/domain, KPI, code-set, and target-reference inputs |
| `tests/` | Unit, contract, integration, and validation tests |
| `docs/` | Requirements, architecture, decisions, and delivery evidence |

## Local commands

```powershell
databricks bundle validate -t dev
databricks bundle deploy -t dev
databricks bundle run -t dev modeling_workflow
databricks bundle run -t dev model_review_app
python -m pytest
```

Before deploying, override all `REQUIRED_*` variables through a target configuration, CLI `--var` arguments, or CI/CD environment configuration. Production deployment also requires an approved service-principal run identity and a protected production workspace root.

