from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
import secrets

ResourceType = Literal["electricity", "gas", "hot_water", "cold_water"]
Unit = Literal["kwh", "m3", "l"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def nid(prefix: str = "") -> str:
    return f"{prefix}{secrets.token_urlsafe(10)}"


@dataclass
class Meter:
    id: str
    name: str
    resourceType: ResourceType
    unit: Unit
    createdAt: str


@dataclass
class Tariff:
    id: str
    resourceType: ResourceType
    currency: Literal["EUR"]
    pricePerUnit: float
    vatRate: float
    updatedAt: str


@dataclass
class Provider:
    id: str
    name: str
    protocol: Literal["mock", "lnd", "core-lightning"]
    health: Literal["healthy", "degraded", "down", "unknown"]
    updatedAt: str


@dataclass
class ConsumptionEvent:
    id: str
    meterId: str
    ts: str
    delta: float
    unit: Unit


@dataclass
class LedgerEntry:
    id: str
    ts: str
    meterId: str
    resourceType: ResourceType
    amountEur: float
    amountSats: int
    reason: Literal["consumption", "settlement_fee"]


@dataclass
class Payment:
    id: str
    ts: str
    providerId: str
    amountSats: int
    feeSats: int
    status: Literal["pending", "settled", "failed"]
    paymentHash: str
    preimage: Optional[str] = None
    memo: Optional[str] = None


@dataclass
class Store:
    meters: List[Meter] = field(default_factory=list)
    tariffs: List[Tariff] = field(default_factory=list)
    providers: List[Provider] = field(default_factory=list)
    consumption: List[ConsumptionEvent] = field(default_factory=list)
    ledger: List[LedgerEntry] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)
    unsettledEurByProviderId: Dict[str, float] = field(default_factory=dict)

    def as_json(self):
        return asdict(self)


def default_store() -> Store:
    provider_id = "utility-demo"

    meters = [
        Meter(id="m-elec", name="Apartment Electricity", resourceType="electricity", unit="kwh", createdAt=now_iso()),
        Meter(id="m-gas", name="Apartment Gas", resourceType="gas", unit="kwh", createdAt=now_iso()),
        Meter(id="m-hw", name="Hot Water", resourceType="hot_water", unit="l", createdAt=now_iso()),
        Meter(id="m-cw", name="Cold Water", resourceType="cold_water", unit="l", createdAt=now_iso()),
    ]

    tariffs = [
        Tariff(id="t-elec", resourceType="electricity", currency="EUR", pricePerUnit=0.35, vatRate=0.19, updatedAt=now_iso()),
        Tariff(id="t-gas", resourceType="gas", currency="EUR", pricePerUnit=0.12, vatRate=0.19, updatedAt=now_iso()),
        Tariff(id="t-hw", resourceType="hot_water", currency="EUR", pricePerUnit=0.004, vatRate=0.07, updatedAt=now_iso()),
        Tariff(id="t-cw", resourceType="cold_water", currency="EUR", pricePerUnit=0.002, vatRate=0.07, updatedAt=now_iso()),
    ]

    providers = [
        Provider(id=provider_id, name="Utility Provider (Demo)", protocol="mock", health="healthy", updatedAt=now_iso()),
    ]

    s = Store(meters=meters, tariffs=tariffs, providers=providers)
    s.unsettledEurByProviderId[provider_id] = 0.0
    return s

