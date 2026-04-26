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
    userId: int
    meterId: str
    ts: str
    delta: float
    unit: Unit


@dataclass
class LedgerEntry:
    id: str
    ts: str
    userId: int
    meterId: str
    resourceType: ResourceType
    amountEur: float
    amountSats: int
    reason: Literal["consumption", "settlement_fee"]


@dataclass
class Payment:
    id: str
    ts: str
    userId: int
    providerId: str
    amountSats: int
    feeSats: int
    status: Literal["pending", "settled", "failed"]
    paymentHash: str
    preimage: Optional[str] = None
    memo: Optional[str] = None


@dataclass
class TariffPoint:
    ts: str
    resourceType: ResourceType
    pricePerUnit: float


@dataclass
class CarbonPricePoint:
    ts: str
    priceEurPerTonne: float


@dataclass
class CarbonTrade:
    id: str
    ts: str
    userId: int
    side: Literal["buy", "sell"]
    tonnes: float
    priceEurPerTonne: float  # display/reference
    notionalSats: int        # settlement currency (Bitcoin)
    reason: str


@dataclass
class CarbonPosition:
    userId: int
    tonnes: float = 0.0
    debtSats: int = 0
    updatedAt: str = ""


@dataclass
class CarbonDecision:
    ts: str
    userId: int
    surplusEur: float
    baselineCostEur: float
    actualCostEur: float
    carbonPriceEurPerTonne: float
    actions: List[Dict]


@dataclass
class Notification:
    id: str
    ts: str
    userId: int
    type: Literal["warning", "info"]
    title: str
    body: str
    read: bool = False


@dataclass
class Store:
    meters: List[Meter] = field(default_factory=list)
    tariffs: List[Tariff] = field(default_factory=list)
    providers: List[Provider] = field(default_factory=list)
    consumption: List[ConsumptionEvent] = field(default_factory=list)
    ledger: List[LedgerEntry] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)
    tariffHistory: List[TariffPoint] = field(default_factory=list)
    carbonPriceHistory: List[CarbonPricePoint] = field(default_factory=list)
    carbonTrades: List[CarbonTrade] = field(default_factory=list)
    carbonPositions: Dict[int, CarbonPosition] = field(default_factory=dict)
    carbonDecisions: List[CarbonDecision] = field(default_factory=list)
    notifications: List[Notification] = field(default_factory=list)
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
    for t in tariffs:
        s.tariffHistory.append(TariffPoint(ts=t.updatedAt, resourceType=t.resourceType, pricePerUnit=t.pricePerUnit))
    # Start with a simple carbon price (EUR / tonne CO2e)
    s.carbonPriceHistory.append(CarbonPricePoint(ts=now_iso(), priceEurPerTonne=80.0))
    s.carbonPositions[1] = CarbonPosition(userId=1, tonnes=0.0, debtSats=0, updatedAt=now_iso())
    s.unsettledEurByProviderId[provider_id] = 0.0
    return s

