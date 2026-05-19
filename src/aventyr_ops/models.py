from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class MonitoringEvent(BaseModel):
    event_id: str
    timestamp: datetime
    site_id: str
    site_name: str
    signal_type: str
    operator_verified: bool
    already_billed: bool
    confidence: float
    notes: str


class CustomerAccount(BaseModel):
    customer_id: str
    customer_name: str
    site_id: str
    site_name: str
    contract_rate_per_verified_alarm: Decimal
    included_confirmed_alarms_per_month: int = 0
    included_confirmed_alarms_used_mtd: int = 0
    billing_cadence: str
    odoo_customer_ref: str


class DisputeRecord(BaseModel):
    event_id: str
    site_id: str
    reason: str
    status: Literal["hold", "resolved", "dismissed"]
    review_owner: str


class WeatherEvent(BaseModel):
    weather_id: str
    timestamp: datetime
    site_id: str
    condition: str
    wind_kph: float
    notes: str


class BillingLineItem(BaseModel):
    event_id: str
    customer_id: str
    customer_name: str
    site_id: str
    site_name: str
    odoo_customer_ref: str
    description: str
    quantity: int = 1
    unit_price: Decimal
    subtotal: Decimal
    contract_rate_basis: str = "confirmed alarm event"
    included_confirmed_alarms_per_month: int = 0
    included_confirmed_alarms_used_mtd: int = 0
    allowance_status: str = "extra confirmed event"


class HeldEvent(BaseModel):
    event_id: str
    site_id: str
    site_name: str
    hold_reason: str
    review_owner: str
    source: str


class CrewTraceStep(BaseModel):
    step: str
    agent_name: str
    action: str
    result: str


class BillingRunResult(BaseModel):
    line_items: list[BillingLineItem] = Field(default_factory=list)
    held_events: list[HeldEvent] = Field(default_factory=list)
    ignored_events: list[str] = Field(default_factory=list)
    crew_trace: list[CrewTraceStep] = Field(default_factory=list)

    @property
    def total_ar(self) -> Decimal:
        return sum((item.subtotal for item in self.line_items), Decimal("0.00"))


class IncidentSample(BaseModel):
    sample_id: str
    site_id: str
    site_name: str
    reported_at: datetime
    message: str


class IncidentClassification(BaseModel):
    sample_id: str
    site_id: str
    site_name: str
    severity: int
    incident_type: str
    route: str
    action_required: str
    audit_fields: dict[str, str]
    retention_note: str


class SiteDemand(BaseModel):
    shift_id: str
    date: str
    site_id: str
    site_name: str
    start_time: str
    end_time: str
    required_certification: str
    priority: str


class GuardProfile(BaseModel):
    guard_id: str
    guard_name: str
    available_date: str
    certifications: list[str]
    home_city: str
    prior_site_experience: str | None
    rotation_score: int
    hourly_rate: Decimal


class GuardCandidate(BaseModel):
    guard_id: str
    guard_name: str
    score: int
    rationale: list[str]
    hourly_rate: Decimal


class GuardCoverageResult(BaseModel):
    shift_id: str
    site_name: str
    required_certification: str
    candidates: list[GuardCandidate]
    audit_summary: str
