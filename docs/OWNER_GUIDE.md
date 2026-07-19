# Agentic Data Analyst and Modeler — Owner Guide

You do not need to memorize the contracts. They are internal safety checks,
similar to building codes: important to the builders, but not the story used to
explain the product.

## The five-step story

1. **Scope** — a person chooses the business area and authorizes the source.
2. **Observe** — the system records metadata, safe profiles and supplied requirements.
3. **Reason** — the AI explains the source and designs the Silver and Gold models and mappings.
4. **Review** — people inspect evidence, correct mistakes and approve material outputs.
5. **Publish** — approved records become Delta-backed deliverables and generated Excel/App views.

## What the AI does

The AI interprets business meaning, compares design alternatives, drafts models
and mappings, finds ambiguity and explains its reasoning with evidence.

## What ordinary code does

Ordinary Python and Databricks enforce access, calculate statistics, validate
completeness, preserve evidence, prevent duplicate records and ensure that only
a human can approve material output.

## What a contract means

A contract is simply a checklist that the software can enforce. For example,
an attribute definition must identify its table and column, distinguish an
observed fact from an inference, cite evidence and carry its review state.

The owner needs to remember only four deliverables:

- Source Data Dictionary;
- Silver ODS model;
- Gold dimensional model; and
- source-to-target mappings.

Everything else exists to make those four deliverables safe, explainable and
repeatable.

## Current proof slice

The current slice is P&C Personal Auto, Policy domain, identified by its solution run,
covering all seven PolicyCenter tables currently present in the authorized source
schema. Scope discovery, registration, metadata capture and DQX profiling are
deployed and repeatably successful. The observed facts are also frozen in one
immutable evidence set, so the work package is now `EVIDENCE_READY`.

In plain English, the system now knows **what exists**: seven tables and 62
attributes. It has safe counts for every attribute and has not stored minimums,
maximums, common values or pattern samples. Running the same input twice produced
one profile snapshot, which is the expected no-duplicate behavior.

The next gate is **what it means**. The owner has approved exact Personal Auto
pack `0.6.0` for runtime selection. Before the AI can draft the dictionary, the
solution still needs the engagement-specific authorization/applicability rule
and the context task that selects only the small Policy-relevant subset.

After that authorization, the remaining owner-visible path is:

1. AI drafts the source dictionary and cites the observed evidence;
2. a person reviews and approves or corrects it;
3. AI drafts Silver, Gold and the mappings from that approved dictionary;
4. people review those designs; and
5. the system publishes the approved package and its coverage/gap report.
