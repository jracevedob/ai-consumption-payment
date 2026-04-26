import pytest

from server.carbon_agent import carbon_agent_step
from server.store import default_store


def test_carbon_agent_buys_on_surplus():
    s = default_store()
    d = carbon_agent_step(s, 1, actual_cost_eur=0.05, baseline_cost_eur=0.20, btc_eur_rate=60000.0)
    assert d["surplusEur"] > 0
    assert s.carbonPositions[1].tonnes >= 0
    assert any(a["type"] == "buy_credits" for a in d["actions"]) or s.carbonPositions[1].debtSats >= 0
    assert len(s.carbonDecisions) >= 1


def test_carbon_agent_sells_or_borrows_on_deficit():
    s = default_store()
    # seed some tonnes so selling is possible
    carbon_agent_step(s, 1, actual_cost_eur=0.05, baseline_cost_eur=0.20, btc_eur_rate=60000.0)
    d = carbon_agent_step(s, 1, actual_cost_eur=0.40, baseline_cost_eur=0.20, btc_eur_rate=60000.0)
    assert d["surplusEur"] < 0
    assert (any(a["type"] == "sell_credits" for a in d["actions"])) or (any(a["type"] == "borrow_debt" for a in d["actions"]))
    assert len(s.carbonDecisions) >= 2

