import { nanoid } from "nanoid";
import type { ConsumptionEvent, LedgerEntry, Meter, Payment, Provider, Tariff } from "./types.js";

type StoreState = {
  meters: Meter[];
  tariffs: Tariff[];
  consumption: ConsumptionEvent[];
  ledger: LedgerEntry[];
  payments: Payment[];
  providers: Provider[];
  unsettledEurByProviderId: Record<string, number>;
};

const nowIso = () => new Date().toISOString();

export class InMemoryStore {
  private state: StoreState;

  constructor() {
    const providerId = "utility-demo";

    const meters: Meter[] = [
      { id: "m-elec", name: "Apartment Electricity", resourceType: "electricity", unit: "kwh", createdAt: nowIso() },
      { id: "m-gas", name: "Apartment Gas", resourceType: "gas", unit: "kwh", createdAt: nowIso() },
      { id: "m-hw", name: "Hot Water", resourceType: "hot_water", unit: "l", createdAt: nowIso() },
      { id: "m-cw", name: "Cold Water", resourceType: "cold_water", unit: "l", createdAt: nowIso() }
    ];

    const tariffs: Tariff[] = [
      { id: "t-elec", resourceType: "electricity", currency: "EUR", pricePerUnit: 0.35, vatRate: 0.19, updatedAt: nowIso() },
      { id: "t-gas", resourceType: "gas", currency: "EUR", pricePerUnit: 0.12, vatRate: 0.19, updatedAt: nowIso() },
      { id: "t-hw", resourceType: "hot_water", currency: "EUR", pricePerUnit: 0.004, vatRate: 0.07, updatedAt: nowIso() },
      { id: "t-cw", resourceType: "cold_water", currency: "EUR", pricePerUnit: 0.002, vatRate: 0.07, updatedAt: nowIso() }
    ];

    const providers: Provider[] = [
      { id: providerId, name: "Utility Provider (Demo)", protocol: "mock", health: "healthy", updatedAt: nowIso() }
    ];

    this.state = {
      meters,
      tariffs,
      consumption: [],
      ledger: [],
      payments: [],
      providers,
      unsettledEurByProviderId: { [providerId]: 0 }
    };
  }

  get snapshot(): Readonly<StoreState> {
    return this.state;
  }

  listMeters() {
    return this.state.meters;
  }

  listTariffs() {
    return this.state.tariffs;
  }

  listProviders() {
    return this.state.providers;
  }

  listConsumption(limit = 200) {
    return this.state.consumption.slice(-limit);
  }

  listLedger(limit = 200) {
    return this.state.ledger.slice(-limit);
  }

  listPayments(limit = 200) {
    return this.state.payments.slice(-limit);
  }

  addConsumption(e: Omit<ConsumptionEvent, "id">) {
    const event: ConsumptionEvent = { ...e, id: nanoid() };
    this.state.consumption.push(event);
    return event;
  }

  addLedgerEntry(e: Omit<LedgerEntry, "id">) {
    const entry: LedgerEntry = { ...e, id: nanoid() };
    this.state.ledger.push(entry);
    return entry;
  }

  addPayment(p: Omit<Payment, "id">) {
    const payment: Payment = { ...p, id: nanoid() };
    this.state.payments.push(payment);
    return payment;
  }

  setProviderHealth(providerId: string, health: Provider["health"]) {
    const p = this.state.providers.find((x) => x.id === providerId);
    if (!p) return;
    p.health = health;
    p.updatedAt = nowIso();
  }

  addUnsettled(providerId: string, amountEur: number) {
    this.state.unsettledEurByProviderId[providerId] ??= 0;
    this.state.unsettledEurByProviderId[providerId] += amountEur;
  }

  takeUnsettled(providerId: string) {
    const v = this.state.unsettledEurByProviderId[providerId] ?? 0;
    this.state.unsettledEurByProviderId[providerId] = 0;
    return v;
  }
}

