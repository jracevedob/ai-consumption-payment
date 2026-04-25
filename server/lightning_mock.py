from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class Invoice:
    invoice: str
    expiresAt: str


@dataclass
class PayResult:
    ok: bool
    status: str
    paymentHash: str
    preimage: str | None = None
    feeSats: int = 0
    reason: str | None = None


class MockLightning:
    async def create_invoice(self, amount_sats: int, memo: str | None = None) -> Invoice:
        token = f"lnmock_{amount_sats}_{secrets.token_urlsafe(10)}"
        exp = datetime.now(timezone.utc) + timedelta(seconds=60)
        return Invoice(invoice=token, expiresAt=exp.isoformat())

    async def pay_invoice(self, invoice: str, amount_sats: int) -> PayResult:
        payment_hash = f"mock_{secrets.token_urlsafe(8)}"
        preimage = f"preimage_{secrets.token_urlsafe(12)}"
        fee = max(1, round(amount_sats * 0.002))
        return PayResult(ok=True, status="settled", paymentHash=payment_hash, preimage=preimage, feeSats=int(fee))

