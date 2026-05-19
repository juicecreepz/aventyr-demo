# Aventyr Ops Command Center

CrewAI-structured Streamlit proof-of-work built against Aventyr Security's public operating model and AI Automation & Operations Engineer role.

This repository is meant to be reviewed as an internal automation slice: deterministic business rules, agent-shaped workflow traces, audit-friendly outputs, and human approval before any live system writeback.

## Demo Video

[Watch the Loom walkthrough](https://www.loom.com/share/a4a65d7d1ef346ef940669dc1d4bf098)

## Reviewer Summary

- Built for the role Aventyr posted: CrewAI, internal tooling, AP/AR, incident reporting, guard scheduling, and business-process automation.
- Uses CrewAI to structure workflows and explain trace steps, not to invent billing, dispatch, or compliance outcomes.
- Keeps the financial path deterministic with `Decimal`, allowance tracking, exception holds, and Odoo-ready export rows.
- Avoids live Odoo, Airtable, Slack, Twilio, or scheduling writes until discovery confirms source-of-truth fields, permissions, and approval rules.
- Includes focused tests, linting, dependency compatibility checks, and a CI workflow.

## What It Demonstrates

This proof-of-work project demonstrates practical workflow understanding across finance, dispatch, and incident operations:

- Verified alarm billing using Aventyr's public `$20` confirmed extra-event basis
- Synthetic account allowance state so included monthly alarms are not silently billed
- Disputed or likely false-trigger event holdbacks
- Odoo-ready AR export
- Incident intake with audit-ready routing and retention fields
- Guard coverage ranking with dispatcher-ready rationale

## Repository Map

```text
src/aventyr_ops/
  app.py                 Streamlit page orchestration and session state
  models.py              Pydantic models for workflow inputs, outputs, and traces
  crews/                 CrewAI workflow definitions plus deterministic logic
  services/              Data loading and export boundaries
  ui/                    Reusable Streamlit UI primitives
data/                    Synthetic workflow inputs
exports/                 Sample generated outputs
tests/                   Focused unit tests for business rules and safety helpers
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the design rationale and production path.

## Runtime

Use Python `>=3.10,<3.14`.

No API keys are required for the current demo. The workflow outputs are deterministic and run entirely from the included synthetic data.

## Setup

```bash
uv sync --extra dev
```

## Verify

```bash
uv run python -m compileall src
uv run ruff check .
uv run pytest -q
uv pip check
```

See [VERIFICATION.md](VERIFICATION.md) for the current verification checklist and browser smoke coverage.

## Run

```bash
uv run streamlit run src/aventyr_ops/app.py --server.port 8501
```

Then open `http://localhost:8501`.

## Demo Boundary

This is a proof-of-work demo using synthetic data. It intentionally avoids live Odoo, Airtable, Slack, or Twilio writes before discovery.

The financial core is deterministic Python for repeatable demo output. CrewAI `Agent`, `Task`, and `Crew` objects are used to structure the workflow and trace, not to invent billing results.

## Productionization Path

The next production iteration would add Odoo draft-invoice creation, Airtable or database-backed review queues, notification handoffs, role-based approvals, idempotency keys, retry/dead-letter handling, structured logs, and vault-backed secrets. The app already keeps those boundaries visible so the prototype can move toward production without rewriting the core business rules.
