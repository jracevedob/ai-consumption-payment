from server.store import default_store


def test_default_store_has_meters_tariffs_provider():
    s = default_store()
    assert len(s.meters) == 4
    assert len(s.tariffs) == 4
    assert len(s.providers) == 1
    pid = s.providers[0].id
    assert pid in s.unsettledEurByProviderId
    assert s.unsettledEurByProviderId[pid] == 0.0

