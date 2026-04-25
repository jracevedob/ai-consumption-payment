from __future__ import annotations

import random
from typing import Dict

from .store import CarbonPricePoint, CarbonTrade, Store, now_iso, nid
from .money import eur_to_sats


def current_carbon_price(store: Store) -> float:
    if not store.carbonPriceHistory:
        store.carbonPriceHistory.append(CarbonPricePoint(ts=now_iso(), priceEurPerTonne=80.0))
    return float(store.carbonPriceHistory[-1].priceEurPerTonne)


def maybe_update_carbon_price(store: Store, tick: int) -> None:
    # Small random walk, to make a realistic-looking chart.
    if tick % 15 != 0:
        return
    p = current_carbon_price(store)
    drift = random.uniform(-0.01, 0.012)
    nxt = max(10.0, p * (1.0 + drift))
    store.carbonPriceHistory.append(CarbonPricePoint(ts=now_iso(), priceEurPerTonne=float(nxt)))


def compute_surplus_eur(
    actual_cost_eur: float,
    baseline_cost_eur: float,
) -> float:
    """
    Positive => saved money (consumed less than baseline)
    Negative => overspent vs baseline (consumed more than baseline)
    """
    return float(baseline_cost_eur - actual_cost_eur)


def carbon_agent_step(
    store: Store,
    user_id: int,
    *,
    actual_cost_eur: float,
    baseline_cost_eur: float,
    btc_eur_rate: float,
    max_debt_sats: int = 50_000,
    invest_fraction: float = 0.8,
) -> Dict:
    """
    Demo policy:
    - If surplus: invest a fraction into carbon credits (buy tonnes).
    - If deficit: either sell existing credits; if still deficit, increase debt (up to cap).
    """
    if user_id not in store.carbonPositions:
        store.carbonPositions[user_id] = store.carbonPositions.get(1)  # fallback

    pos = store.carbonPositions[user_id]
    price = current_carbon_price(store)
    surplus = compute_surplus_eur(actual_cost_eur, baseline_cost_eur)

    decision = {
        "userId": user_id,
        "ts": now_iso(),
        "carbonPriceEurPerTonne": price,
        "surplusEur": surplus,
        "actions": [],
        "settlementCurrency": "sats",
    }

    # Use existing debt repayment if we have surplus (debt is in sats)
    if surplus > 0 and pos.debtSats > 0:
        repay_sats = min(int(pos.debtSats), eur_to_sats(surplus * 0.5, btc_eur_rate))
        pos.debtSats = int(pos.debtSats - repay_sats)
        decision["actions"].append({"type": "repay_debt", "amountSats": repay_sats})

    if surplus > 0:
        budget_eur = surplus * invest_fraction
        budget_sats = eur_to_sats(budget_eur, btc_eur_rate)
        tonnes = budget_eur / price if price > 0 else 0.0
        if tonnes > 0:
            trade = CarbonTrade(
                id=nid("ct_"),
                ts=decision["ts"],
                userId=user_id,
                side="buy",
                tonnes=float(tonnes),
                priceEurPerTonne=float(price),
                notionalSats=int(budget_sats),
                reason="invest_surplus",
            )
            store.carbonTrades.append(trade)
            pos.tonnes = float(pos.tonnes + tonnes)
            pos.updatedAt = decision["ts"]
            decision["actions"].append({"type": "buy_credits", "tonnes": tonnes, "notionalSats": budget_sats})
        return decision

    if surplus < 0:
        need_eur = -surplus
        need_sats = eur_to_sats(need_eur, btc_eur_rate)
        # Sell credits first
        if pos.tonnes > 0 and price > 0:
            sell_tonnes = min(pos.tonnes, need_eur / price)
            if sell_tonnes > 0:
                notional_eur = sell_tonnes * price
                notional_sats = eur_to_sats(notional_eur, btc_eur_rate)
                trade = CarbonTrade(
                    id=nid("ct_"),
                    ts=decision["ts"],
                    userId=user_id,
                    side="sell",
                    tonnes=float(sell_tonnes),
                    priceEurPerTonne=float(price),
                    notionalSats=int(notional_sats),
                    reason="cover_deficit",
                )
                store.carbonTrades.append(trade)
                pos.tonnes = float(pos.tonnes - sell_tonnes)
                pos.updatedAt = decision["ts"]
                need_sats = max(0, int(need_sats - notional_sats))
                decision["actions"].append({"type": "sell_credits", "tonnes": sell_tonnes, "notionalSats": notional_sats})

        # If still need coverage, increase debt (demo)
        if need_sats > 0:
            headroom = max(0, int(max_debt_sats - pos.debtSats))
            borrow = min(headroom, int(need_sats))
            if borrow > 0:
                pos.debtSats = int(pos.debtSats + borrow)
                pos.updatedAt = decision["ts"]
                decision["actions"].append({"type": "borrow_debt", "amountSats": borrow})

        return decision

    return decision

