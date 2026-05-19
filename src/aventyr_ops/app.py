from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from aventyr_ops.config import DATA_DIR, EXPORT_DIR
from aventyr_ops.crews.alarm_billing import (
    build_alarm_billing_crew,
    build_approval_summary,
    prepare_alarm_billing_run,
)
from aventyr_ops.crews.guard_coverage import (
    build_guard_coverage_crew,
    rank_guard_coverage,
)
from aventyr_ops.crews.incident_intake import (
    build_incident_intake_crew,
    classify_incident,
)
from aventyr_ops.services.data_loader import (
    load_customer_accounts,
    load_dispute_records,
    load_guard_pool,
    load_incident_samples,
    load_monitoring_events,
    load_site_demand,
    load_weather_events,
)
from aventyr_ops.services.exports import (
    write_audit_log,
    write_held_events_export,
    write_odoo_ar_export,
)
from aventyr_ops.ui.components import (
    BRAND,
    humanize_key,
    page_chrome,
    records_table,
    sidebar_brand,
    sidebar_foot,
    sidebar_section,
    wb_banner,
    wb_buckets,
    wb_candidate_row,
    wb_files_panel,
    wb_footnote,
    wb_head,
    wb_inbound_bubble,
    wb_kpi_row,
    wb_master_table,
    wb_packet,
    wb_readiness_grid,
    wb_section,
    wb_severity_panel,
    wb_signal_cards,
    wb_toolbar,
    wb_work_order,
    wb_work_strip,
)

STEP_TITLES = {
    "Verified Alarm Pull Agent": "Pull verified events",
    "Account Match Agent": "Match accounts",
    "Dispute Flag Agent": "Hold exceptions",
    "Approval Summary Agent": "Prepare batch",
    "Intake Agent": "Receive guard report",
    "Classification Agent": "Classify severity",
    "Routing Agent": "Route and write audit",
    "Coverage Gap Agent": "Read open shift",
    "Ranking Agent": "Rank eligible guards",
    "Dispatcher Summary Agent": "Hand to dispatcher",
}


PAGES = [
    "Alarm Billing",
    "Incident Intake",
    "Guard Coverage",
    "Readiness",
]


def main() -> None:
    page_chrome()
    page = _render_sidebar()

    if page == "Alarm Billing":
        render_billing()
    elif page == "Incident Intake":
        render_incident()
    elif page == "Guard Coverage":
        render_guard()
    elif page == "Readiness":
        render_readiness()


def _render_sidebar() -> str:
    sidebar_brand()
    sidebar_section("Workflows")
    page = st.sidebar.radio(
        "Workflow",
        PAGES,
        label_visibility="collapsed",
        key="active_page",
    )
    sidebar_foot(
        "<b>Synthetic data only.</b><br>"
        "No live writes. Manual approval before any Odoo writeback."
    )
    return page


def _now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d · %H:%M")


# ============== Alarm Billing ==============

def render_billing() -> None:
    events = load_monitoring_events(DATA_DIR / "monitoring_queue.csv")
    accounts = load_customer_accounts(DATA_DIR / "customer_accounts.csv")
    disputes = load_dispute_records(DATA_DIR / "dispute_log.csv")
    weather = load_weather_events(DATA_DIR / "weather_events.csv")
    crew = build_alarm_billing_crew()
    result, exports = _ensure_billing_run(events, accounts, disputes, weather)

    verified_unbilled = sum(1 for e in events if e.operator_verified and not e.already_billed)

    crumb = (
        'Workflows <span class="sep">/</span> <b>Alarm Billing</b> '
        f'<span class="sep">/</span> Run {_now_label()}'
    )
    wb_toolbar(crumb, "Synthetic · live")

    col_l, col_r = st.columns([1, 0.18])
    with col_l:
        wb_head(
            deck=f'Billing run <b>· {_now_label()}</b>',
            title="12 alarm events reviewed. 8 ready for billing. 2 held for review.",
            body=(
                "Verified alarm events filtered, matched to Aventyr customer accounts, checked "
                "against included monthly allowance state, rated at Aventyr's public $20 per confirmed "
                "extra event, and held when disputed, tied to weather, or tied to equipment. "
                "Approval batch and audit log written for finance review."
            ),
        )
    with col_r:
        st.markdown(
            '<div style="padding: 1.4rem 1.6rem 0; display:flex; justify-content:flex-end; gap:0.5rem;">',
            unsafe_allow_html=True,
        )
        if st.button("Rerun", type="primary", key="run_billing"):
            result, exports = _run_billing(events, accounts, disputes, weather)
        st.markdown('</div>', unsafe_allow_html=True)

    wb_kpi_row(
        [
            ("Reviewed", str(len(events)), "from monitoring queue", ""),
            ("Verified unbilled", str(verified_unbilled), "before exceptions", "cyan"),
            ("Billable", str(len(result.line_items)), "ready for approval", "ok"),
            ("Held", str(len(result.held_events)), "before invoice review", "warn"),
            ("Approval batch", f"${result.total_ar:.2f}", "Odoo CSV written", ""),
        ]
    )

    wb_section("Run records", meta=f"{len(events)} events · grouped by status")
    wb_buckets(
        [
            ("Billable", len(result.line_items), f"${result.total_ar:.2f} approval batch", "ok"),
            ("Held", len(result.held_events), "before invoice review", "warn"),
            (
                "Skipped",
                len(events) - len(result.line_items) - len(result.held_events),
                "not eligible this run",
                "skip",
            ),
        ]
    )
    wb_master_table(_build_master_rows(events, result))

    wb_section("Workflow", meta=f"{len(crew.agents)} agents · sequential")
    wb_work_strip(
        [
            (
                "01",
                "Pull verified events",
                "10 candidates from the 12-event monitoring queue, filtering for verified, unbilled signals.",
            ),
            (
                "02",
                "Match to accounts",
                "Site identifiers joined to Aventyr customer accounts, allowance state, and Odoo customer references.",
            ),
            (
                "03",
                "Hold exceptions",
                "Disputes, wind correlation above 50 kph, and equipment risk signals stop before billing.",
            ),
            ("04", "Prepare batch", "AR lines for approval, queue of held events, and audit log written."),
        ]
    )

    wb_section("Export files", meta="written to ./exports/")
    wb_files_panel(
        [
            ("Odoo AR", _short_path(exports["Odoo AR export"]), f"{len(result.line_items)} rows"),
            ("Held events", _short_path(exports["Held events export"]), f"{len(result.held_events)} rows"),
            ("Audit log", _short_path(exports["Audit log"]), f"{len(result.crew_trace)} rows"),
        ]
    )

    with st.expander("Approval summary text", expanded=False):
        st.code(build_approval_summary(result), language="text")
    with st.expander(f"Source monitoring queue · {len(events)} synthetic events", expanded=False):
        st.dataframe(records_table(events), width="stretch", hide_index=True)

    wb_footnote(
        "Synthetic data only. No live Odoo, Airtable, Slack, Twilio, or customer writes before discovery. "
        "Aventyr's public $20 per confirmed extra event is represented with synthetic allowance state; "
        "the hold logic and manual approval stay in the loop."
    )


def _build_master_rows(events, result) -> list[dict]:
    billable_ids = {item.event_id: item for item in result.line_items}
    held_ids = {ev.event_id: ev for ev in result.held_events}
    ignored_map = {line.split(":")[0].strip(): line.split(":", 1)[1].strip() for line in result.ignored_events}

    billable_rows: list[dict] = []
    held_rows: list[dict] = []
    skipped_rows: list[dict] = []
    for event in events:
        eid = event.event_id
        if eid in billable_ids:
            item = billable_ids[eid]
            billable_rows.append({
                "id": eid,
                "status_kind": "ok",
                "status_label": "BILLABLE",
                "customer": item.customer_name,
                "site": item.site_name,
                "reason": None,
                "owner": "Finance review",
                "amount": f"${item.subtotal:.2f}",
            })
        elif eid in held_ids:
            ev = held_ids[eid]
            held_rows.append({
                "id": eid,
                "status_kind": "warn",
                "status_label": "HELD",
                "customer": ev.site_name,
                "site": None,
                "reason": ev.hold_reason,
                "owner": ev.review_owner,
                "amount": "hold",
                "amount_state": "hold",
            })
        else:
            reason = ignored_map.get(eid, "Not eligible")
            skipped_rows.append({
                "id": eid,
                "status_kind": "skip",
                "status_label": "SKIPPED",
                "customer": event.site_name,
                "site": None,
                "reason": reason,
                "owner": "—",
                "amount": "—",
                "amount_state": "muted",
            })

    rows: list[dict] = []
    for label, group in (
        (f"Billable · {len(billable_rows)}", billable_rows),
        (f"Held · {len(held_rows)}", held_rows),
        (f"Skipped · {len(skipped_rows)}", skipped_rows),
    ):
        if not group:
            continue
        rows.append({"group_break": True, "label": label})
        rows.extend(group)
    return rows


def _short_path(full_path: str) -> str:
    """Display a friendly project-relative export path."""
    return f"./exports/{Path(full_path).name}"


def _ensure_billing_run(events, accounts, disputes, weather):
    result = st.session_state.get("billing_result")
    exports = st.session_state.get("billing_exports")
    if result is None or exports is None:
        return _run_billing(events, accounts, disputes, weather)
    return result, exports


def _run_billing(events, accounts, disputes, weather):
    result = prepare_alarm_billing_run(events, accounts, disputes, weather)
    ar_path = write_odoo_ar_export(result, EXPORT_DIR)
    held_path = write_held_events_export(result, EXPORT_DIR)
    audit_path = write_audit_log(result, EXPORT_DIR)
    exports = {
        "Odoo AR export": str(ar_path),
        "Held events export": str(held_path),
        "Audit log": str(audit_path),
    }
    st.session_state["billing_result"] = result
    st.session_state["billing_exports"] = exports
    return result, exports


# ============== Incident Intake ==============

def render_incident() -> None:
    samples = load_incident_samples(DATA_DIR / "incident_samples.json")
    crew = build_incident_intake_crew()

    crumb = (
        'Workflows <span class="sep">/</span> <b>Incident Intake</b> '
        f'<span class="sep">/</span> {_now_label()}'
    )
    wb_toolbar(crumb, "Synthetic · live")

    wb_head(
        deck="Guard reports / severity routing",
        title="Turn a messy guard report into the next operator decision.",
        body=(
            "Classifies severity, decides who needs the next alert, and packages the audit fields "
            "a supervisor would need before the record enters the compliance binder."
        ),
    )
    wb_kpi_row(
        [
            ("Sample reports", str(len(samples)), "synthetic guard messages", ""),
            ("Agents", str(len(crew.agents)), "intake / classify / route", ""),
            ("Audit fields", "5", "timestamp / signal / action / tier / route", "cyan"),
            ("Severity scale", "1-5", "nuisance to emergency", ""),
        ]
    )

    wb_section("Inbound guard report")
    st.markdown('<div class="wb-toolbar-pad"></div>', unsafe_allow_html=True)
    col_select, col_btn, _ = st.columns([0.7, 0.2, 1])
    with col_select:
        sample_labels = {f"{s.sample_id} / {s.site_name}": s for s in samples}
        selected = st.selectbox("Sample incident", list(sample_labels.keys()), label_visibility="collapsed")
        sample = sample_labels[selected]
    with col_btn:
        clicked = st.button("Reclassify", type="primary", key="run_incident")

    wb_inbound_bubble(
        f"GUARD / {sample.site_name} / {sample.reported_at.strftime('%Y-%m-%d %H:%M %Z').strip()}",
        sample.message,
    )

    if clicked:
        classification, trace = classify_incident(sample)
        st.session_state["incident_result"] = classification
        st.session_state["incident_trace"] = trace
        st.session_state["incident_source_id"] = sample.sample_id
    else:
        classification, trace = _ensure_incident_classification(sample)

    stored_id = st.session_state.get("incident_source_id")
    classification = _current_selection_value(sample.sample_id, stored_id, st.session_state.get("incident_result"))
    trace = _current_selection_value(sample.sample_id, stored_id, st.session_state.get("incident_trace"))

    wb_section("Triage outcome", meta=f"{sample.sample_id} / {sample.site_name}")
    wb_severity_panel(
        severity=classification.severity,
        incident_type=classification.incident_type,
        site=classification.site_name,
        rows=[
            ("Routed to", classification.route),
            ("Action", classification.action_required),
            ("Audit fields", f"{len(classification.audit_fields)} · shape ready for the binder"),
            ("Retention", classification.retention_note),
        ],
    )

    with st.expander("Audit fields", expanded=False):
        st.dataframe(
            pd.DataFrame(
                [(humanize_key(k), v) for k, v in classification.audit_fields.items()],
                columns=["Field", "Value"],
            ),
            width="stretch",
            hide_index=True,
        )
        st.caption(classification.retention_note)
    if trace:
        with st.expander("Crew trace", expanded=False):
            for step in trace:
                st.markdown(
                    f'<div style="padding: 0.4rem 0; border-bottom: 1px solid {BRAND["hair"]}">'
                    f'<span style="color:{BRAND["cyan"]};font-family:JetBrains Mono,monospace;font-size:0.78rem">'
                    f'{step.step}</span> · <b>{step.agent_name}</b><br>'
                    f'<span style="color:{BRAND["ink_3"]};font-size:0.85rem">{step.result}</span></div>',
                    unsafe_allow_html=True,
                )

    wb_footnote(
        "Synthetic data only. No live Slack, Twilio, or dispatch routing. "
        "Audit fields shape only — final retention follows Aventyr's compliance binder."
    )


# ============== Guard Coverage ==============

def render_guard() -> None:
    shifts = load_site_demand(DATA_DIR / "site_demand.csv")
    guards = load_guard_pool(DATA_DIR / "guard_pool.csv")
    crew = build_guard_coverage_crew()

    crumb = (
        'Workflows <span class="sep">/</span> <b>Guard Coverage</b> '
        f'<span class="sep">/</span> {_now_label()}'
    )
    wb_toolbar(crumb, "Synthetic · live")

    wb_head(
        deck="Coverage gap / dispatcher support",
        title="Produce a shortlist a dispatcher can use, not just a score.",
        body=(
            "Filters by required certification, then ranks by site experience, proximity, rotation "
            "fairness, and cost. The system explains its tradeoffs; it does not assign automatically."
        ),
    )
    wb_kpi_row(
        [
            ("Open shifts", str(len(shifts)), "needing coverage", "warn"),
            ("Available guards", str(len(guards)), "in pool", ""),
            ("Agents", str(len(crew.agents)), "coverage / rank / summarize", ""),
            ("Ranking factors", "4", "cert / proximity / history / fairness", "cyan"),
        ]
    )

    wb_section("Coverage gap")
    st.markdown('<div class="wb-toolbar-pad"></div>', unsafe_allow_html=True)
    col_select, col_btn, _ = st.columns([0.7, 0.2, 1])
    with col_select:
        shift_labels = {f"{s.shift_id} / {s.site_name}": s for s in shifts}
        selected = st.selectbox("Coverage gap", list(shift_labels.keys()), label_visibility="collapsed")
        shift = shift_labels[selected]
    with col_btn:
        clicked = st.button("Rerank", type="primary", key="run_coverage")

    wb_work_order(shift)

    if clicked:
        coverage, trace = rank_guard_coverage(shift, guards)
        st.session_state["coverage_result"] = coverage
        st.session_state["coverage_trace"] = trace
        st.session_state["coverage_shift_id"] = shift.shift_id
    else:
        coverage, trace = _ensure_guard_coverage(shift, guards)

    stored_id = st.session_state.get("coverage_shift_id")
    coverage = _current_selection_value(shift.shift_id, stored_id, st.session_state.get("coverage_result"))
    trace = _current_selection_value(shift.shift_id, stored_id, st.session_state.get("coverage_trace"))

    top_candidate = coverage.candidates[0] if coverage.candidates else None
    wb_section("Coverage outcome", meta=f"{shift.shift_id} / {shift.required_certification} required")
    wb_signal_cards(
        [
            ("Required cert", coverage.required_certification, "hard eligibility filter", "cyan"),
            (
                "Top option",
                top_candidate.guard_name if top_candidate else "Escalate",
                "dispatcher still approves",
                "ok" if top_candidate else "warn",
            ),
            (
                "Eligible guards",
                str(len(coverage.candidates)),
                "ranked by fit and fairness",
                "ok" if coverage.candidates else "warn",
            ),
        ]
    )

    wb_section("Dispatcher decision packet")
    if top_candidate:
        wb_packet(
            [
                ("Work order", f"{shift.shift_id} / {shift.site_name} / {shift.start_time}-{shift.end_time}"),
                ("Recommendation", f"{top_candidate.guard_name} at score {top_candidate.score}"),
                ("Why this guard", list(top_candidate.rationale)),
                (
                    "Control",
                    "Dispatcher keeps final assignment control. Ranking supports the decision but does not make it.",
                ),
            ]
        )
    else:
        wb_packet(
            [
                ("Work order", f"{shift.shift_id} / {shift.site_name} / {shift.start_time}-{shift.end_time}"),
                ("Recommendation", "Escalate to dispatcher"),
                ("Why", "No certified guards available for this shift in the synthetic pool."),
                ("Control", "Dispatcher keeps final assignment control."),
            ]
        )

    wb_section(
        "Dispatcher shortlist",
        meta=f"{coverage.required_certification} required / top {len(coverage.candidates)}",
    )
    if not coverage.candidates:
        wb_banner("No certified guards available for this shift. Dispatcher escalation required.", kind="warn")
    for i, candidate in enumerate(coverage.candidates, start=1):
        wb_candidate_row(i, candidate, is_top=(i == 1))
    wb_banner(coverage.audit_summary, kind="ok")

    with st.expander("Guard pool · 6 synthetic profiles", expanded=False):
        st.dataframe(records_table(guards), width="stretch", hide_index=True)
    if trace:
        with st.expander("Crew trace", expanded=False):
            for step in trace:
                st.markdown(
                    f'<div style="padding: 0.4rem 0; border-bottom: 1px solid {BRAND["hair"]}">'
                    f'<span style="color:{BRAND["cyan"]};font-family:JetBrains Mono,monospace;font-size:0.78rem">'
                    f'{step.step}</span> · <b>{step.agent_name}</b><br>'
                    f'<span style="color:{BRAND["ink_3"]};font-size:0.85rem">{step.result}</span></div>',
                    unsafe_allow_html=True,
                )

    wb_footnote(
        "Synthetic data only. No live dispatch. Final assignment stays with the dispatcher; ranking "
        "supports the decision but does not make it."
    )


# ============== Readiness ==============

def render_readiness() -> None:
    crumb = (
        'Workflows <span class="sep">/</span> <b>Readiness</b> '
        '<span class="sep">/</span> Boundary'
    )
    wb_toolbar(crumb, "Synthetic · live")

    wb_head(
        deck="Path from demo to production",
        title="What changes between this proof and a live Aventyr workflow.",
        body=(
            "Each group below maps to a hardening step before any live customer write. "
            "The current build is a bounded synthetic data proof."
        ),
    )
    wb_kpi_row(
        [
            ("Live writes", "0", "this build", ""),
            ("Sources", "CSV", "to be replaced", ""),
            ("Approval gate", "Manual", "stays in the loop", "cyan"),
            ("Contract terms", "Allowance aware", "synthetic account state", ""),
        ]
    )

    wb_section("Week one implementation path")
    wb_work_strip(
        [
            (
                "01",
                "Map sources",
                "Confirm Airtable, Odoo, monitoring exports, contract allowance terms, and field owners before touching live data.",
            ),
            (
                "02",
                "Run shadow mode",
                "Produce approval batches beside the current process with no customer or accounting writes.",
            ),
            (
                "03",
                "Review exceptions",
                "Tune the hold rules with supervisors so disputes and false triggers stay protected.",
            ),
            ("04", "Gate writeback", "Only then add idempotent Odoo draft creation behind manual approval."),
        ]
    )

    wb_section("Hardening groups")
    wb_readiness_grid(
        [
            (
                "Data sources",
                [
                    "Replace CSVs with Aventyr Airtable, Odoo, or monitoring exports.",
                    (
                        "Map signal types, site IDs, verification status, included alarms, "
                        "and rates for extra events from the source of truth."
                    ),
                ],
            ),
            (
                "Odoo writeback",
                [
                    "Map export columns to invoice draft or sales order line items.",
                    "Idempotent post by event_id; never bill a verified alarm twice.",
                ],
            ),
            (
                "Retention and compliance",
                [
                    "Align audit retention fields with Aventyr's compliance binder.",
                    "Confirm BC private security retention windows before storing live records.",
                ],
            ),
            (
                "Human review",
                [
                    "Approval step before any accounting writeback.",
                    "Role-based review for hold categories (weather, equipment, dispute).",
                ],
            ),
            (
                "Monitoring and retries",
                [
                    "Log each run, exceptions, held events, and export status.",
                    "Retry policy and dead-letter queue for failed records.",
                ],
            ),
            (
                "Deployment",
                [
                    "Package as internal Streamlit app or private workflow service.",
                    "Secrets via env or vault; no client data committed to source control.",
                ],
            ),
        ]
    )

    wb_footnote(
        "Synthetic data only. No live Odoo, Airtable, Slack, Twilio, or customer writes before discovery. "
        "Aventyr's public $20 per confirmed extra event is represented with synthetic allowance state; "
        "the hold logic and manual approval stay in the loop."
    )


def _current_selection_value(current_id, stored_id, value):
    return value if current_id == stored_id else None


def _ensure_incident_classification(sample):
    if st.session_state.get("incident_source_id") != sample.sample_id:
        classification, trace = classify_incident(sample)
        st.session_state["incident_result"] = classification
        st.session_state["incident_trace"] = trace
        st.session_state["incident_source_id"] = sample.sample_id
    return st.session_state["incident_result"], st.session_state["incident_trace"]


def _ensure_guard_coverage(shift, guards):
    if st.session_state.get("coverage_shift_id") != shift.shift_id:
        coverage, trace = rank_guard_coverage(shift, guards)
        st.session_state["coverage_result"] = coverage
        st.session_state["coverage_trace"] = trace
        st.session_state["coverage_shift_id"] = shift.shift_id
    return st.session_state["coverage_result"], st.session_state["coverage_trace"]


if __name__ == "__main__":
    main()
