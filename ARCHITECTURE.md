# Architecture

This project is a focused proof-of-work for Aventyr Security's AI Automation & Operations Engineer role. It shows how agent-shaped workflows can reduce manual operations work without letting an LLM invent financial, dispatch, or compliance outcomes.

## Design Principles

- Deterministic core, agent-shaped workflow: CrewAI `Agent`, `Task`, and `Crew` objects describe the operating process, while Python business rules produce the actual results.
- Human approval before live writes: the app creates review packets, exports, rankings, and audit trails, but it does not write to Odoo, Airtable, Slack, Twilio, or scheduling systems.
- Auditability over magic: every workflow exposes inputs, decisions, exceptions, and next actions.
- Synthetic data only: the repository includes enough sample data to verify behavior without committing customer, employee, or site-sensitive records.
- Replaceable boundaries: data loading and exports are isolated so real adapters can be added without rewriting the business logic.

## Workflow Map

### Alarm Billing Crew

Purpose: prepare verified alarm-event billing for finance review.

The workflow:

1. Loads monitoring events, customer account allowance state, dispute records, and weather signals.
2. Filters for operator-verified, unbilled events.
3. Matches billable events to account and Odoo references.
4. Holds disputed, equipment-related, or weather-correlated events before invoice writeback.
5. Produces an Odoo-ready AR export, held-event export, audit log, and approval summary.

The financial path uses `Decimal`, included-allowance tracking, and explicit hold reasons because billing correctness matters more than generative flexibility.

### Incident Intake Crew

Purpose: turn field reports into audit-ready incident classifications.

The workflow:

1. Preserves the original synthetic report and site context.
2. Assigns severity and incident type from deterministic rules.
3. Produces route, action-required, response-tier, and retention fields for review.

This mirrors the job requirement around incident reporting, HR/compliance-style document workflows, and operational triage.

### Guard Coverage Crew

Purpose: help dispatch review uncovered shifts.

The workflow:

1. Reads a synthetic open shift.
2. Filters available guards by date and required certification.
3. Scores candidates by certification, site history, proximity, fairness, and rate.
4. Presents a dispatcher-ready shortlist while keeping final assignment with a human.

This is intentionally a recommendation workflow, not an auto-assignment workflow.

### Readiness Page

Purpose: make the production boundary explicit.

The page explains what is running now, what would need discovery, and how the demo would become a live internal tool.

## Module Layout

- `src/aventyr_ops/models.py`: typed Pydantic models for workflow inputs, outputs, and trace records.
- `src/aventyr_ops/services/data_loader.py`: CSV and JSON loading boundaries.
- `src/aventyr_ops/services/exports.py`: export writers for AR lines, held events, and audit logs.
- `src/aventyr_ops/crews/`: CrewAI workflow definitions plus deterministic business logic.
- `src/aventyr_ops/app.py`: Streamlit page orchestration and session state.
- `src/aventyr_ops/ui/components.py`: reusable Streamlit UI primitives and output encoding helpers.
- `tests/`: focused tests for billing, exports, incident routing, guard ranking, and UI helper safety.

## Data And Security Boundary

- No real customer data is committed.
- No API keys are required.
- `.env` and `.env.*` are ignored.
- Dynamic HTML values are escaped before rendering in custom Streamlit components.
- Live writebacks are intentionally absent until source-of-truth systems, permissions, and approval rules are confirmed.

## Production Path

The next production iteration would add:

- Odoo draft invoice adapter with idempotency keys and human approval states.
- Airtable or internal database adapter for workflow state and review queues.
- Zapier, Slack, SMS, or Twilio notifications for approved handoffs only.
- Role-based access control for finance, dispatch, and management actions.
- Retry and dead-letter handling for failed external writes.
- Structured application logs, run IDs, and export retention policies.
- Secrets management through environment variables or a vault, never committed source.
- CI-backed linting and tests on every repository change.

## Known Tradeoffs

This is a proof-of-work repository, not a finished production deployment. Streamlit was chosen because the role calls out internal tools and quick operational interfaces. The current UI layer is intentionally local and portable for review; a production version would split the larger UI module into smaller components and introduce authentication, authorization, and deployment-specific security headers.
