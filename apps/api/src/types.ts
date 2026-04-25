export type ResourceType = "electricity" | "gas" | "hot_water" | "cold_water";

export type Meter = {
  id: string;
  name: string;
  resourceType: ResourceType;
  unit: "kwh" | "m3" | "l";
  createdAt: string;
};

export type ConsumptionEvent = {
  id: string;
  meterId: string;
  ts: string;
  delta: number;
  unit: Meter["unit"];
};

export type Tariff = {
  id: string;
  resourceType: ResourceType;
  currency: "EUR";
  pricePerUnit: number; // EUR per kwh/m3/l
  vatRate: number; // 0..1
  updatedAt: string;
};

export type LedgerEntry = {
  id: string;
  ts: string;
  meterId: string;
  resourceType: ResourceType;
  amountEur: number;
  amountSats: number;
  reason: "consumption" | "settlement_fee";
};

export type Payment = {
  id: string;
  ts: string;
  providerId: string;
  amountSats: number;
  feeSats: number;
  status: "pending" | "settled" | "failed";
  paymentHash: string;
  preimage?: string;
  memo?: string;
};

export type Provider = {
  id: string;
  name: string;
  protocol: "mock" | "lnd" | "core-lightning";
  health: "healthy" | "degraded" | "down" | "unknown";
  updatedAt: string;
};

