from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

from aventyr_ops.models import BillingRunResult


def write_odoo_ar_export(result: BillingRunResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "odoo_ar_export.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "odoo_customer_ref",
                "customer_name",
                "site_name",
                "event_id",
                "description",
                "quantity",
                "unit_price",
                "subtotal",
                "contract_rate_basis",
                "included_confirmed_alarms_per_month",
                "included_confirmed_alarms_used_mtd",
                "allowance_status",
            ],
        )
        writer.writeheader()
        for item in result.line_items:
            writer.writerow(
                {
                    "odoo_customer_ref": item.odoo_customer_ref,
                    "customer_name": item.customer_name,
                    "site_name": item.site_name,
                    "event_id": item.event_id,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": f"{item.unit_price:.2f}",
                    "subtotal": f"{item.subtotal:.2f}",
                    "contract_rate_basis": item.contract_rate_basis,
                    "included_confirmed_alarms_per_month": item.included_confirmed_alarms_per_month,
                    "included_confirmed_alarms_used_mtd": item.included_confirmed_alarms_used_mtd,
                    "allowance_status": item.allowance_status,
                }
            )
    return path


def write_held_events_export(result: BillingRunResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "held_events.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["event_id", "site_id", "site_name", "hold_reason", "review_owner", "source"],
        )
        writer.writeheader()
        for event in result.held_events:
            writer.writerow(event.model_dump())
    return path


def write_audit_log(result: BillingRunResult, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "billing_run_audit_log.csv"
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp", "crew_name", "step", "agent_name", "action", "result"],
        )
        writer.writeheader()
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for step in result.crew_trace:
            writer.writerow(
                {
                    "timestamp": timestamp,
                    "crew_name": "Alarm Billing Crew",
                    "step": step.step,
                    "agent_name": step.agent_name,
                    "action": step.action,
                    "result": step.result,
                }
            )
    return path
