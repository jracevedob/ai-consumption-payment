from __future__ import annotations

from .store import ResourceType, Tariff


def compute_cost_eur(resource_type: ResourceType, delta: float, tariff: Tariff) -> float:
    base = delta * tariff.pricePerUnit
    total = base * (1.0 + tariff.vatRate)
    return float(total)

