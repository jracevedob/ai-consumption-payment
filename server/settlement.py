from __future__ import annotations

import asyncio
from typing import Optional

from .lightning_mock import MockLightning
from .money import eur_to_sats
from .store import ConsumptionEvent, LedgerEntry, Payment, Store, now_iso, nid
from .tariff import compute_cost_eur
from .budget import monthly_budget_snapshot
from .carbon_agent import carbon_agent_step
from .store import Notification


def apply_latest_consumption(store: Store, provider_id: str, btc_eur_rate: float) -> float:
    """
    Apply only the most recent tick's worth of consumption (1 event per meter).
    Returns the unsettled EUR balance after applying.
    """
    latest = store.consumption[-len(store.meters) :] if store.meters else []
    if not latest:
        return store.unsettledEurByProviderId.get(provider_id, 0.0)

    tariffs_by_rt = {t.resourceType: t for t in store.tariffs}
    meters_by_id = {m.id: m for m in store.meters}

    for e in latest:
        m = meters_by_id.get(e.meterId)
        if m is None:
            continue
        t = tariffs_by_rt.get(m.resourceType)
        if t is None:
            continue
        cost_eur = compute_cost_eur(m.resourceType, e.delta, t)
        store.unsettledEurByProviderId[provider_id] = store.unsettledEurByProviderId.get(provider_id, 0.0) + cost_eur
        store.ledger.append(
            LedgerEntry(
                id=nid(),
                ts=e.ts,
                userId=e.userId,
                meterId=e.meterId,
                resourceType=m.resourceType,
                amountEur=cost_eur,
                amountSats=eur_to_sats(cost_eur, btc_eur_rate),
                reason="consumption",
            )
        )

    return store.unsettledEurByProviderId.get(provider_id, 0.0)


async def maybe_settle(
    store: Store,
    provider_id: str,
    user_id: int,
    btc_eur_rate: float,
    threshold_eur: float,
    lightning: MockLightning,
) -> Optional[Payment]:
    unsettled = store.unsettledEurByProviderId.get(provider_id, 0.0)
    if unsettled < threshold_eur:
        return None

    store.unsettledEurByProviderId[provider_id] = 0.0
    amount_sats = eur_to_sats(unsettled, btc_eur_rate)

    inv = await lightning.create_invoice(amount_sats, memo="utility settlement")
    res = await lightning.pay_invoice(inv.invoice, amount_sats)
    ts = now_iso()

    if res.ok:
        p = Payment(
            id=nid(),
            ts=ts,
            userId=user_id,
            providerId=provider_id,
            amountSats=amount_sats,
            feeSats=res.feeSats,
            status="settled",
            paymentHash=res.paymentHash,
            preimage=res.preimage,
            memo="auto-settlement",
        )
        store.payments.append(p)
        if res.feeSats > 0:
            store.ledger.append(
                LedgerEntry(
                    id=nid(),
                    ts=ts,
                    userId=user_id,
                    meterId="system",
                    resourceType="electricity",
                    amountEur=0.0,
                    amountSats=res.feeSats,
                    reason="settlement_fee",
                )
            )
        return p

    # failed: retry later by restoring unsettled
    store.unsettledEurByProviderId[provider_id] = store.unsettledEurByProviderId.get(provider_id, 0.0) + unsettled
    p = Payment(
        id=nid(),
        ts=ts,
        userId=user_id,
        providerId=provider_id,
        amountSats=amount_sats,
        feeSats=0,
        status="failed",
        paymentHash=res.paymentHash,
        memo=res.reason or "payment failed",
    )
    store.payments.append(p)
    return p


def wire_tick(store: Store, provider_id: str, btc_eur_rate: float, threshold_eur: float, lightning: MockLightning):
    """
    Returns a callback suitable for the simulator which schedules settlement.
    """

    def _on_tick():
        apply_latest_consumption(store, provider_id, btc_eur_rate)
        # Warmmiete budget model (default 73/27 split). For now use fallback values if user has no profile persisted.
        warmmiete_eur = 1000.0
        utilities_share = 0.27
        snap = monthly_budget_snapshot(store, 1, warmmiete_eur=warmmiete_eur, utilities_share=utilities_share)

        # Use budget-to-date as baseline for carbon agent; actual-to-date comes from ledger.
        carbon_agent_step(
            store,
            user_id=1,
            actual_cost_eur=snap.utilitiesActualToDateEur,
            baseline_cost_eur=snap.utilitiesBudgetToDateEur,
            btc_eur_rate=btc_eur_rate,
        )

        # Notify on deficit beyond small tolerance.
        if snap.surplusEur < -0.10:
            store.notifications.append(
                Notification(
                    id=nid("n_"),
                    ts=now_iso(),
                    userId=1,
                    type="warning",
                    title="Utility deficit vs Warmmiete prepayment",
                    body=f"This month you are over your prepaid utilities by €{abs(snap.surplusEur):.2f}. Consider reducing usage or switching tariffs.",
                    read=False,
                )
            )
        asyncio.create_task(maybe_settle(store, provider_id, 1, btc_eur_rate, threshold_eur, lightning))

    return _on_tick

