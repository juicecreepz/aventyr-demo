# Verification

Run these checks before sharing or deploying the repository.

```bash
uv sync --extra dev
uv run python -m compileall src
uv run ruff check .
uv run pytest -q
uv pip check
```

## Current Local Verification

Last verification date: 2026-05-19.

| Check | Command | Result |
| --- | --- | --- |
| Package compile | `uv run python -m compileall src` | passed |
| Lint | `uv run ruff check .` | passed, all checks clean |
| Unit tests | `uv run pytest -q` | passed, 12 tests |
| Dependency compatibility | `uv pip check` | passed, all installed packages compatible |

CrewAI currently emits deprecation warnings from its installed dependency internals during tests. The warnings do not come from failing application behavior, but they are worth monitoring before a production dependency pin.

## Browser Smoke Coverage

The Streamlit app should also be smoke-tested locally:

```bash
uv run streamlit run src/aventyr_ops/app.py --server.port 8501
```

Then open `http://localhost:8501` and verify:

- Alarm Billing loads, produces the AR total, shows holdbacks, and exposes exports.
- Incident Intake changes classification when a different sample is selected.
- Guard Coverage changes the candidate shortlist when a different shift is selected.
- Readiness explains demo boundaries, live-write blockers, and production next steps.
- Mobile width does not overlap the sidebar, tables, controls, or primary content.

Latest local browser smoke: passed on port `8502` because `8501` was already occupied. Playwright CLI snapshots covered Alarm Billing, Incident Intake, Guard Coverage, Readiness, mobile `390x844`, and browser console output reported `0` errors and `0` warnings.

This repository does not include live Odoo, Airtable, Slack, Twilio, or scheduling credentials. That is intentional: the safe production next step is a draft-only adapter with idempotency, audit logging, and human approval.
