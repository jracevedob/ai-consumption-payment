import type { InMemoryStore } from "./store.js";

const rand = (min: number, max: number) => Math.random() * (max - min) + min;

export function startSimulation(params: {
  store: InMemoryStore;
  providerId: string;
  tickMs: number;
  onTick?: () => void;
}) {
  const { store, tickMs, onTick, providerId } = params;

  const timer = setInterval(() => {
    const meters = store.listMeters();
    for (const m of meters) {
      let delta = 0;
      if (m.resourceType === "electricity") delta = rand(0.01, 0.08); // kWh
      if (m.resourceType === "gas") delta = rand(0.02, 0.12); // kWh
      if (m.resourceType === "hot_water") delta = rand(0.2, 2.5); // liters
      if (m.resourceType === "cold_water") delta = rand(0.3, 3.2); // liters

      store.addConsumption({
        meterId: m.id,
        ts: new Date().toISOString(),
        delta,
        unit: m.unit
      });
    }

    // Keep provider health “mostly healthy” but occasionally degraded for UI.
    const r = Math.random();
    if (r < 0.02) store.setProviderHealth(providerId, "degraded");
    else if (r < 0.025) store.setProviderHealth(providerId, "down");
    else store.setProviderHealth(providerId, "healthy");

    onTick?.();
  }, tickMs);

  return () => clearInterval(timer);
}

