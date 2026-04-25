export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:4000";

async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

export type Stats = {
  endpointsIndexed: number;
  paymentVerified: number;
  providersIndexed: number;
  providersVerified: number;
  healthy: number;
  degraded: number;
  down: number;
  unknown: number;
  lastCheckedAt: string;
  unsettledEur: number;
};

export type Provider = {
  id: string;
  name: string;
  protocol: string;
  health: "healthy" | "degraded" | "down" | "unknown";
  updatedAt: string;
};

export type Meter = {
  id: string;
  name: string;
  resourceType: string;
  unit: string;
  createdAt: string;
};

export type Payment = {
  id: string;
  ts: string;
  providerId: string;
  amountSats: number;
  feeSats: number;
  status: string;
  paymentHash: string;
  memo?: string;
};

export async function getStats() {
  return apiGet<Stats>("/v1/stats");
}

export async function getProviders() {
  return apiGet<Provider[]>("/v1/providers");
}

export async function getMeters() {
  return apiGet<Meter[]>("/v1/meters");
}

export async function getPayments() {
  return apiGet<Payment[]>("/v1/payments");
}

