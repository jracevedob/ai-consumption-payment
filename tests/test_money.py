from server.money import eur_to_sats


def test_eur_to_sats_zero_and_positive():
    assert eur_to_sats(0.0, 60000.0) == 0
    assert eur_to_sats(1.0, 50000.0) == 2000  # 1/50000 BTC = 2e-5 BTC = 2000 sats


def test_eur_to_sats_never_negative():
    assert eur_to_sats(-1.0, 60000.0) == 0

