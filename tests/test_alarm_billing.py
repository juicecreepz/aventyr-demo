import csv
from decimal import Decimal

from aventyr_ops.config import DATA_DIR
from aventyr_ops.crews.alarm_billing import (
    build_alarm_billing_crew,
    build_approval_summary,
    prepare_alarm_billing_run,
)
from aventyr_ops.services.data_loader import (
    load_customer_accounts,
    load_dispute_records,
    load_monitoring_events,
    load_weather_events,
)
from aventyr_ops.services.exports import (
    write_audit_log,
    write_held_events_export,
    write_odoo_ar_export,
)


def test_loads_alarm_billing_data():
    events = load_monitoring_events(DATA_DIR / "monitoring_queue.csv")
    accounts = load_customer_accounts(DATA_DIR / "customer_accounts.csv")
    disputes = load_dispute_records(DATA_DIR / "dispute_log.csv")
    weather = load_weather_events(DATA_DIR / "weather_events.csv")

    assert len(events) == 12
    assert len(accounts) == 4
    assert len(disputes) == 2
    assert len(weather) == 2
    assert events[0].operator_verified is True
    assert events[4].operator_verified is False
    assert accounts[0].contract_rate_per_verified_alarm == Decimal("20.00")
    assert accounts[0].included_confirmed_alarms_per_month == 4
    assert accounts[0].included_confirmed_alarms_used_mtd == 4


def _load_inputs():
    return (
        load_monitoring_events(DATA_DIR / "monitoring_queue.csv"),
        load_customer_accounts(DATA_DIR / "customer_accounts.csv"),
        load_dispute_records(DATA_DIR / "dispute_log.csv"),
        load_weather_events(DATA_DIR / "weather_events.csv"),
    )


def test_alarm_billing_run_creates_ar_lines_and_holds_exceptions():
    result = prepare_alarm_billing_run(*_load_inputs())

    assert len(result.line_items) == 8
    assert result.total_ar == Decimal("160.00")
    assert len(result.held_events) == 2
    assert len(result.ignored_events) == 2
    assert {event.event_id for event in result.held_events} == {"EVT-1008", "EVT-1010"}
    assert all(item.unit_price == Decimal("20.00") for item in result.line_items)
    assert "Verified Alarm Pull Agent" in {step.agent_name for step in result.crew_trace}


def test_alarm_billing_exports_odoo_ready_files(tmp_path):
    result = prepare_alarm_billing_run(*_load_inputs())

    ar_path = write_odoo_ar_export(result, tmp_path)
    held_path = write_held_events_export(result, tmp_path)
    audit_path = write_audit_log(result, tmp_path)

    with ar_path.open() as handle:
        ar_rows = list(csv.DictReader(handle))
    with held_path.open() as handle:
        held_rows = list(csv.DictReader(handle))
    with audit_path.open() as handle:
        audit_rows = list(csv.DictReader(handle))

    assert len(ar_rows) == 8
    assert ar_rows[0]["odoo_customer_ref"].startswith("ODOO-")
    assert ar_rows[0]["unit_price"] == "20.00"
    assert ar_rows[0]["contract_rate_basis"] == "confirmed alarm event beyond included monthly allowance"
    assert ar_rows[0]["allowance_status"] == "included allowance already consumed"
    assert len(held_rows) == 2
    assert len(audit_rows) == 4
    assert audit_rows[0]["crew_name"] == "Alarm Billing Crew"


def test_alarm_billing_respects_remaining_included_allowance():
    events, accounts, disputes, weather = _load_inputs()
    account = accounts[0].model_copy(
        update={
            "included_confirmed_alarms_per_month": 4,
            "included_confirmed_alarms_used_mtd": 3,
        }
    )

    result = prepare_alarm_billing_run([events[0]], [account], disputes, weather)

    assert result.line_items == []
    assert result.total_ar == Decimal("0.00")
    assert result.ignored_events == ["EVT-1001: covered by included monthly alarm allowance"]


def test_approval_summary_is_human_review_oriented():
    result = prepare_alarm_billing_run(*_load_inputs())
    summary = build_approval_summary(result)

    assert "Approval total: $160.00" in summary
    assert "Human review required" in summary


def test_crewai_crew_objects_are_available_for_demo_trace():
    crew = build_alarm_billing_crew()

    assert len(crew.agents) == 4
    assert len(crew.tasks) == 4
    assert crew.agents[0].role == "Verified Alarm Pull Agent"
