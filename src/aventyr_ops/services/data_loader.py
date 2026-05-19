from __future__ import annotations

import csv
import json
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from aventyr_ops.models import (
    CustomerAccount,
    DisputeRecord,
    GuardProfile,
    IncidentSample,
    MonitoringEvent,
    SiteDemand,
    WeatherEvent,
)

T = TypeVar("T")


def _read_csv(path: Path, factory: Callable[[dict[str, str]], T]) -> list[T]:
    with path.open(newline="") as handle:
        return [factory(row) for row in csv.DictReader(handle)]


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"true", "1", "yes"}


def load_monitoring_events(path: Path) -> list[MonitoringEvent]:
    return _read_csv(
        path,
        lambda row: MonitoringEvent(
            **{
                **row,
                "operator_verified": _parse_bool(row["operator_verified"]),
                "already_billed": _parse_bool(row["already_billed"]),
                "confidence": float(row["confidence"]),
            }
        ),
    )


def load_customer_accounts(path: Path) -> list[CustomerAccount]:
    return _read_csv(path, lambda row: CustomerAccount(**row))


def load_dispute_records(path: Path) -> list[DisputeRecord]:
    return _read_csv(path, lambda row: DisputeRecord(**row))


def load_weather_events(path: Path) -> list[WeatherEvent]:
    return _read_csv(path, lambda row: WeatherEvent(**row))


def load_incident_samples(path: Path) -> list[IncidentSample]:
    with path.open() as handle:
        rows = json.load(handle)
    return [IncidentSample(**row) for row in rows]


def load_site_demand(path: Path) -> list[SiteDemand]:
    return _read_csv(path, lambda row: SiteDemand(**row))


def load_guard_pool(path: Path) -> list[GuardProfile]:
    def factory(row: dict[str, str]) -> GuardProfile:
        certifications = [item.strip() for item in row["certifications"].split(";") if item.strip()]
        prior_site_experience = row["prior_site_experience"].strip() or None
        return GuardProfile(
            **{
                **row,
                "certifications": certifications,
                "prior_site_experience": prior_site_experience,
            }
        )

    return _read_csv(path, factory)

