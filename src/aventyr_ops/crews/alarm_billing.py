from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from crewai import Agent, Crew, Process, Task

from aventyr_ops.models import (
    BillingLineItem,
    BillingRunResult,
    CrewTraceStep,
    CustomerAccount,
    DisputeRecord,
    HeldEvent,
    MonitoringEvent,
    WeatherEvent,
)


def build_alarm_billing_crew() -> Crew:
    """Create CrewAI objects used to describe the deterministic workflow."""
    verified_alarm_agent = Agent(
        role="Verified Alarm Pull Agent",
        goal="Find verified unbilled monitoring events that should enter AR review.",
        backstory="A finance-aware monitoring assistant that never bills unverified or duplicate events.",
        llm=None,
    )
    account_match_agent = Agent(
        role="Account Match Agent",
        goal="Match verified alarm events to customer accounts and contract rates.",
        backstory="An Odoo handoff specialist that keeps customer references and site mappings clean.",
        llm=None,
    )
    dispute_flag_agent = Agent(
        role="Dispute Flag Agent",
        goal="Hold events that may be false triggers, tied to weather, disputed, or tied to equipment.",
        backstory="A cautious reviewer that protects client trust before line items reach invoices.",
        llm=None,
    )
    approval_agent = Agent(
        role="Approval Summary Agent",
        goal="Prepare a human-readable billing batch summary for finance review.",
        backstory="A practical operator that keeps humans in the loop before accounting writeback.",
        llm=None,
    )

    tasks = [
        Task(
            description="Pull verified, unbilled alarm events from the synthetic monitoring queue.",
            expected_output="A list of candidate verified alarm events.",
            agent=verified_alarm_agent,
        ),
        Task(
            description="Match each candidate event to an Aventyr customer account and contract rate.",
            expected_output="Odoo-ready AR line item candidates.",
            agent=account_match_agent,
        ),
        Task(
            description="Flag disputed, weather-correlated, or equipment issue events for human review.",
            expected_output="A held-events list with review reasons.",
            agent=dispute_flag_agent,
        ),
        Task(
            description="Prepare the billing batch summary and approval-ready totals.",
            expected_output="A concise approval summary for review.",
            agent=approval_agent,
        ),
    ]
    return Crew(
        agents=[
            verified_alarm_agent,
            account_match_agent,
            dispute_flag_agent,
            approval_agent,
        ],
        tasks=tasks,
        process=Process.sequential,
        verbose=False,
    )


def prepare_alarm_billing_run(
    events: list[MonitoringEvent],
    accounts: list[CustomerAccount],
    disputes: list[DisputeRecord],
    weather_events: list[WeatherEvent],
) -> BillingRunResult:
    result = BillingRunResult()
    account_by_site = {account.site_id: account for account in accounts}
    disputes_by_event = {dispute.event_id: dispute for dispute in disputes if dispute.status == "hold"}
    allowance_remaining_by_site = {
        account.site_id: max(
            account.included_confirmed_alarms_per_month - account.included_confirmed_alarms_used_mtd,
            0,
        )
        for account in accounts
    }

    candidates = [event for event in events if is_billable_event(event)]
    result.crew_trace.append(
        CrewTraceStep(
            step="1",
            agent_name="Verified Alarm Pull Agent",
            action="Filtered monitoring queue for verified and unbilled events.",
            result=f"{len(candidates)} candidate events found from {len(events)} total events.",
        )
    )

    for event in events:
        if not event.operator_verified:
            result.ignored_events.append(f"{event.event_id}: not operator verified")
        elif event.already_billed:
            result.ignored_events.append(f"{event.event_id}: already billed")

    for event in candidates:
        account = account_by_site.get(event.site_id)
        if account is None:
            result.held_events.append(
                HeldEvent(
                    event_id=event.event_id,
                    site_id=event.site_id,
                    site_name=event.site_name,
                    hold_reason="No customer account mapping found for site.",
                    review_owner="Finance review",
                    source="account-match",
                )
            )
            continue

        held_event = should_hold_event(event, disputes_by_event, weather_events)
        if held_event is not None:
            result.held_events.append(held_event)
            continue

        if allowance_remaining_by_site.get(account.site_id, 0) > 0:
            allowance_remaining_by_site[event.site_id] -= 1
            result.ignored_events.append(f"{event.event_id}: covered by included monthly alarm allowance")
            continue

        result.line_items.append(create_line_item(event, account))

    result.crew_trace.extend(
        [
            CrewTraceStep(
                step="2",
                agent_name="Account Match Agent",
                action="Joined candidate events to customer accounts, allowance state, and Odoo references.",
                result=f"{len(result.line_items) + len(result.held_events)} candidate events mapped or held.",
            ),
            CrewTraceStep(
                step="3",
                agent_name="Dispute Flag Agent",
                action="Checked dispute log, equipment notes, and wind-correlated events.",
                result=f"{len(result.held_events)} events held before invoice review.",
            ),
            CrewTraceStep(
                step="4",
                agent_name="Approval Summary Agent",
                action="Prepared approval-ready AR total and held-event exceptions.",
                result=f"{len(result.line_items)} line items totaling ${result.total_ar:.2f}.",
            ),
        ]
    )
    return result


def is_billable_event(event: MonitoringEvent) -> bool:
    return event.operator_verified and not event.already_billed


def should_hold_event(
    event: MonitoringEvent,
    disputes_by_event: dict[str, DisputeRecord],
    weather_events: list[WeatherEvent],
) -> HeldEvent | None:
    dispute = disputes_by_event.get(event.event_id)
    if dispute is not None:
        return HeldEvent(
            event_id=event.event_id,
            site_id=event.site_id,
            site_name=event.site_name,
            hold_reason=dispute.reason,
            review_owner=dispute.review_owner,
            source="dispute-log",
        )

    lowered_notes = event.notes.lower()
    if (
        "equipment issue" in lowered_notes
        or "hardware failure" in lowered_notes
        or "camera tamper" in event.signal_type.lower()
    ):
        return HeldEvent(
            event_id=event.event_id,
            site_id=event.site_id,
            site_name=event.site_name,
            hold_reason="Equipment-related signal should be reviewed before billing.",
            review_owner="Operations review",
            source="equipment-rule",
        )

    if "wind" in event.signal_type.lower() or "wind" in event.notes.lower():
        matching_weather = [
            weather
            for weather in weather_events
            if weather.site_id == event.site_id
            and weather.condition.lower() == "wind"
            and weather.wind_kph >= 50
        ]
        if matching_weather:
            weather = matching_weather[0]
            return HeldEvent(
                event_id=event.event_id,
                site_id=event.site_id,
                site_name=event.site_name,
                hold_reason=f"Wind-correlated event near {weather.wind_kph:.0f} kph gusts.",
                review_owner="Monitoring supervisor",
                source="weather-correlation",
            )
    return None


def create_line_item(event: MonitoringEvent, account: CustomerAccount) -> BillingLineItem:
    rate = account.contract_rate_per_verified_alarm.quantize(Decimal("0.01"))
    return BillingLineItem(
        event_id=event.event_id,
        customer_id=account.customer_id,
        customer_name=account.customer_name,
        site_id=event.site_id,
        site_name=event.site_name,
        odoo_customer_ref=account.odoo_customer_ref,
        description=f"Verified alarm event {event.event_id} at {event.site_name}",
        unit_price=rate,
        subtotal=rate,
        contract_rate_basis="confirmed alarm event beyond included monthly allowance",
        included_confirmed_alarms_per_month=account.included_confirmed_alarms_per_month,
        included_confirmed_alarms_used_mtd=account.included_confirmed_alarms_used_mtd,
        allowance_status="included allowance already consumed",
    )


def build_approval_summary(result: BillingRunResult) -> str:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return "\n".join(
        [
            f"Generated: {generated_at}",
            f"Billable verified alarms: {len(result.line_items)}",
            f"Held for review: {len(result.held_events)}",
            f"Ignored as non-billable/duplicate: {len(result.ignored_events)}",
            f"Approval total: ${result.total_ar:.2f}",
            "Human review required before Odoo writeback.",
        ]
    )
