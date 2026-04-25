import type { InMemoryStore } from "./store.js";
import { computeCostEur } from "./tariff.js";
import { eurToSats } from "./money.js";
import type { MockLightningClient } from "./lightning/mock.js";

export function applyConsumptionAndMaybeSettle(params: {
  store: InMemoryStore;
  providerId: string;
  btcEurRate: number;
  settlementThresholdEur: number;
  lightning: MockLightningClient;
}) {
  const { store, providerId, btcEurRate, settlementThresholdEur, lightning } = params;

  const latest = store.listConsumption(10_000).slice(-store.listMeters().length);
  if (latest.length === 0) return;

  const tariffs = store.listTariffs();
  for (const e of latest) {
    const m = store.listMeters().find((x) => x.id === e.meterId);
    if (!m) continue;
    const t = tariffs.find((x) => x.resourceType === m.resourceType);
    if (!t) continue;
    const costEur = computeCostEur({ resourceType: m.resourceType, delta: e.delta, tariff: t });
    store.addUnsettled(providerId, costEur);
    store.addLedgerEntry({
      ts: e.ts,
      meterId: e.meterId,
      resourceType: m.resourceType,
      amountEur: costEur,
      amountSats: eurToSats(costEur, btcEurRate),
      reason: "consumption"
    });
  }

  const unsettled = store.snapshot.unsettledEurByProviderId[providerId] ?? 0;
  if (unsettled < settlementThresholdEur) return;

  void (async () => {
    const toSettleEur = store.takeUnsettled(providerId);
    const amountSats = eurToSats(toSettleEur, btcEurRate);
    const { invoice } = await lightning.createInvoice({ amountSats, memo: "utility settlement" });
    const res = await lightning.payInvoice({ invoice, amountSats });
    const ts = new Date().toISOString();

    if (res.ok) {
      store.addPayment({
        ts,
        providerId,
        amountSats,
        feeSats: res.feeSats,
        status: "settled",
        paymentHash: res.paymentHash,
        preimage: res.preimage,
        memo: "auto-settlement"
      });
      if (res.feeSats > 0) {
        store.addLedgerEntry({
          ts,
          meterId: "system",
          resourceType: "electricity",
          amountEur: 0,
          amountSats: res.feeSats,
          reason: "settlement_fee"
        });
      }
    } else {
      store.addPayment({
        ts,
        providerId,
        amountSats,
        feeSats: 0,
        status: "failed",
        paymentHash: res.paymentHash,
        memo: res.reason
      });
      // Put it back so we retry later
      store.addUnsettled(providerId, toSettleEur);
    }
  })();
}

