import { nanoid } from "nanoid";

export type PayInvoiceResult =
  | { ok: true; status: "settled"; paymentHash: string; preimage: string; feeSats: number }
  | { ok: false; status: "failed"; paymentHash: string; reason: string };

export class MockLightningClient {
  async payInvoice(params: { invoice: string; amountSats: number }) : Promise<PayInvoiceResult> {
    // Deterministic-enough “instant settlement” with tiny fee.
    const paymentHash = `mock_${nanoid(10)}`;
    const preimage = `preimage_${nanoid(16)}`;
    const feeSats = Math.max(1, Math.round(params.amountSats * 0.002));
    return { ok: true, status: "settled", paymentHash, preimage, feeSats };
  }

  async createInvoice(params: { amountSats: number; memo?: string }) {
    // This is not a real BOLT11 invoice; for demo we return a token-like string.
    const token = `lnmock_${params.amountSats}_${nanoid(12)}`;
    return { invoice: token, expiresAt: new Date(Date.now() + 60_000).toISOString() };
  }
}

