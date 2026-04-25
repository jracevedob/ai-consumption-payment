import type { ResourceType, Tariff } from "./types.js";

export function computeCostEur(params: { resourceType: ResourceType; delta: number; tariff: Tariff }) {
  const { delta, tariff } = params;
  const base = delta * tariff.pricePerUnit;
  const total = base * (1 + tariff.vatRate);
  return total;
}

