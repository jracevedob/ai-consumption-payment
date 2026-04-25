from server.store import Tariff
from server.tariff import compute_cost_eur


def test_compute_cost_eur_includes_vat():
    t = Tariff(
        id="t",
        resourceType="electricity",
        currency="EUR",
        pricePerUnit=0.35,
        vatRate=0.19,
        updatedAt="now",
    )
    cost = compute_cost_eur("electricity", 2.0, t)  # 2 kWh
    assert abs(cost - (2.0 * 0.35 * 1.19)) < 1e-12

