import pytest

from server.lightning_mock import MockLightning
from server.money import eur_to_sats
from server.settlement import apply_latest_consumption, maybe_settle
from server.store import ConsumptionEvent, default_store, now_iso, nid


def test_apply_latest_consumption_adds_ledger_and_unsettled():
    s = default_store()
    pid = s.providers[0].id

    # Create one event per meter (what simulator does)
    for m in s.meters:
        s.consumption.append(ConsumptionEvent(id=nid(), userId=1, meterId=m.id, ts=now_iso(), delta=1.0, unit=m.unit))

    before_ledger = len(s.ledger)
    before_unsettled = s.unsettledEurByProviderId[pid]

    after_unsettled = apply_latest_consumption(s, pid, btc_eur_rate=60000.0)

    assert len(s.ledger) == before_ledger + len(s.meters)
    assert after_unsettled > before_unsettled
    assert s.unsettledEurByProviderId[pid] == after_unsettled
    assert all(le.reason == "consumption" for le in s.ledger[-len(s.meters) :])


@pytest.mark.asyncio
async def test_maybe_settle_sets_payment_and_resets_unsettled():
    s = default_store()
    pid = s.providers[0].id
    ln = MockLightning()

    s.unsettledEurByProviderId[pid] = 1.0
    p = await maybe_settle(s, pid, 1, btc_eur_rate=50000.0, threshold_eur=0.1, lightning=ln)

    assert p is not None
    assert p.status == "settled"
    assert p.amountSats == eur_to_sats(1.0, 50000.0)
    assert s.unsettledEurByProviderId[pid] == 0.0
    assert len(s.payments) >= 1


@pytest.mark.asyncio
async def test_maybe_settle_noop_below_threshold():
    s = default_store()
    pid = s.providers[0].id
    ln = MockLightning()

    s.unsettledEurByProviderId[pid] = 0.05
    p = await maybe_settle(s, pid, 1, btc_eur_rate=60000.0, threshold_eur=0.1, lightning=ln)
    assert p is None
    assert s.unsettledEurByProviderId[pid] == 0.05

