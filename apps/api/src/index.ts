import "dotenv/config";
import Fastify from "fastify";
import cors from "@fastify/cors";
import { TypeBoxTypeProvider } from "@fastify/type-provider-typebox";
import { Type } from "@sinclair/typebox";
import { InMemoryStore } from "./store.js";
import { MockLightningClient } from "./lightning/mock.js";
import { startSimulation } from "./simulator.js";
import { applyConsumptionAndMaybeSettle } from "./settlement.js";

const PORT = Number(process.env.PORT ?? "4000");
const CORS_ORIGIN = process.env.CORS_ORIGIN ?? "http://localhost:3000";

const SIMULATION_ENABLED = (process.env.SIMULATION_ENABLED ?? "true") === "true";
const SIMULATION_TICK_MS = Number(process.env.SIMULATION_TICK_MS ?? "1500");
const SETTLEMENT_THRESHOLD_EUR = Number(process.env.SETTLEMENT_THRESHOLD_EUR ?? "0.1");
const BTC_EUR_RATE = Number(process.env.BTC_EUR_RATE ?? "60000");

const store = new InMemoryStore();
const lightning = new MockLightningClient();
const providerId = store.listProviders()[0]?.id ?? "utility-demo";

const fastify = Fastify({ logger: true }).withTypeProvider<TypeBoxTypeProvider>();
await fastify.register(cors, { origin: CORS_ORIGIN });

fastify.get("/health", async () => ({ ok: true }));

fastify.get(
  "/v1/stats",
  {
    schema: {
      response: {
        200: Type.Object({
          endpointsIndexed: Type.Number(),
          paymentVerified: Type.Number(),
          providersIndexed: Type.Number(),
          providersVerified: Type.Number(),
          healthy: Type.Number(),
          degraded: Type.Number(),
          down: Type.Number(),
          unknown: Type.Number(),
          lastCheckedAt: Type.String(),
          unsettledEur: Type.Number()
        })
      }
    }
  },
  async () => {
    const providers = store.listProviders();
    const counts = { healthy: 0, degraded: 0, down: 0, unknown: 0 } as Record<string, number>;
    for (const p of providers) counts[p.health] += 1;

    const endpointsIndexed = store.listMeters().length * 4;
    const paymentVerified = store.listPayments().filter((p) => p.status === "settled").length;

    return {
      endpointsIndexed,
      paymentVerified,
      providersIndexed: providers.length,
      providersVerified: providers.filter((p) => p.protocol !== "mock").length,
      ...counts,
      lastCheckedAt: new Date().toISOString(),
      unsettledEur: store.snapshot.unsettledEurByProviderId[providerId] ?? 0
    };
  }
);

fastify.get("/v1/providers", async () => store.listProviders());
fastify.get("/v1/meters", async () => store.listMeters());
fastify.get("/v1/tariffs", async () => store.listTariffs());
fastify.get("/v1/consumption", async () => store.listConsumption(200));
fastify.get("/v1/ledger", async () => store.listLedger(200));
fastify.get("/v1/payments", async () => store.listPayments(200));

fastify.post(
  "/v1/ingest",
  {
    schema: {
      body: Type.Object({
        meterId: Type.String(),
        delta: Type.Number(),
        ts: Type.Optional(Type.String())
      })
    }
  },
  async (req) => {
    const m = store.listMeters().find((x) => x.id === req.body.meterId);
    if (!m) return fastify.httpErrors.notFound("meter not found");
    const ev = store.addConsumption({
      meterId: req.body.meterId,
      delta: req.body.delta,
      ts: req.body.ts ?? new Date().toISOString(),
      unit: m.unit
    });
    return { ok: true, event: ev };
  }
);

let stopSim: undefined | (() => void);
if (SIMULATION_ENABLED) {
  stopSim = startSimulation({
    store,
    providerId,
    tickMs: SIMULATION_TICK_MS,
    onTick: () =>
      applyConsumptionAndMaybeSettle({
        store,
        providerId,
        btcEurRate: BTC_EUR_RATE,
        settlementThresholdEur: SETTLEMENT_THRESHOLD_EUR,
        lightning
      })
  });
}

fastify.addHook("onClose", async () => {
  stopSim?.();
});

await fastify.listen({ port: PORT, host: "0.0.0.0" });

