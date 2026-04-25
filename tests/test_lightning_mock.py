import pytest

from server.lightning_mock import MockLightning


@pytest.mark.asyncio
async def test_mock_lightning_create_and_pay():
    ln = MockLightning()
    inv = await ln.create_invoice(1234, memo="x")
    assert inv.invoice.startswith("lnmock_1234_")
    assert "T" in inv.expiresAt  # iso-like

    res = await ln.pay_invoice(inv.invoice, 1234)
    assert res.ok is True
    assert res.status == "settled"
    assert res.paymentHash.startswith("mock_")
    assert res.preimage is not None
    assert res.feeSats >= 1

