import { Card, Kpi, Pill } from "../components/ui";
import { getMeters, getPayments, getProviders, getStats } from "../lib/api";

function healthTone(h: string) {
  if (h === "healthy") return "green";
  if (h === "degraded") return "yellow";
  if (h === "down") return "red";
  return "gray";
}

export default async function Page() {
  const [stats, providers, meters, payments] = await Promise.all([getStats(), getProviders(), getMeters(), getPayments()]);

  return (
    <div className="min-h-screen bg-white">
      <div className="border-b border-zinc-200 bg-white">
        <div className="container-max mx-auto flex h-14 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-zinc-900" />
            <div className="text-sm font-semibold">Consumption Index</div>
          </div>
          <div className="hidden items-center gap-6 text-sm text-zinc-600 md:flex">
            <a className="hover:text-zinc-900" href="#">
              Overview
            </a>
            <a className="hover:text-zinc-900" href="#">
              Directory
            </a>
            <a className="hover:text-zinc-900" href="#">
              About
            </a>
            <a className="hover:text-zinc-900" href="#">
              Verify API
            </a>
          </div>
          <div className="text-xs text-zinc-500">Hack-Nation demo</div>
        </div>
      </div>

      <div className="container-max mx-auto px-4 py-10">
        <div className="flex flex-col gap-2">
          <div className="text-3xl font-semibold tracking-tight">Real-time utility micro-settlement</div>
          <div className="text-sm text-zinc-600">
            Live metering → deterministic tariffing → automatic settlement over Lightning (mock provider enabled).
          </div>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <Kpi label="Endpoints Indexed" value={stats.endpointsIndexed.toLocaleString()} />
          </Card>
          <Card>
            <Kpi label="Payment-Verified" value={stats.paymentVerified.toLocaleString()} />
          </Card>
          <Card>
            <Kpi label="Providers Indexed" value={stats.providersIndexed.toLocaleString()} />
          </Card>
          <Card>
            <Kpi label="Healthy" value={stats.healthy.toLocaleString()} />
          </Card>
        </div>

        <div className="mt-10 flex items-center gap-2 text-sm font-medium text-zinc-900">
          <div className="rounded-full bg-zinc-900 px-3 py-1 text-white">L402 (Lightning)</div>
          <div className="rounded-full bg-zinc-100 px-3 py-1 text-zinc-700">x402</div>
          <div className="rounded-full bg-zinc-100 px-3 py-1 text-zinc-700">MPP</div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-2">
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">Providers</div>
              <div className="text-xs text-zinc-500">Last checked: {new Date(stats.lastCheckedAt).toLocaleString()}</div>
            </div>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full border-separate border-spacing-0 text-sm">
                <thead>
                  <tr className="text-left text-xs font-semibold text-zinc-500">
                    <th className="pb-3">Name</th>
                    <th className="pb-3">Protocol</th>
                    <th className="pb-3">Health</th>
                    <th className="pb-3">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {providers.map((p) => (
                    <tr key={p.id} className="border-t border-zinc-100">
                      <td className="py-3 font-medium text-zinc-900">{p.name}</td>
                      <td className="py-3 text-zinc-700">{p.protocol}</td>
                      <td className="py-3">
                        <Pill tone={healthTone(p.health)}>{p.health}</Pill>
                      </td>
                      <td className="py-3 text-zinc-600">{new Date(p.updatedAt).toLocaleTimeString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card>
            <div className="text-sm font-semibold">Live settlement</div>
            <div className="mt-2 text-xs text-zinc-500">Unsettled balance (EUR)</div>
            <div className="mt-1 text-3xl font-semibold tracking-tight">€{stats.unsettledEur.toFixed(2)}</div>
            <div className="mt-6 text-xs font-semibold text-zinc-500">Recent payments</div>
            <div className="mt-3 flex flex-col gap-3">
              {payments.slice(-5).reverse().map((p) => (
                <div key={p.id} className="flex items-center justify-between gap-3 rounded-xl border border-zinc-200 p-3">
                  <div className="min-w-0">
                    <div className="truncate text-xs font-medium text-zinc-900">{p.paymentHash}</div>
                    <div className="text-xs text-zinc-500">{new Date(p.ts).toLocaleTimeString()}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-semibold text-zinc-900">{p.amountSats} sats</div>
                    <div className="text-xs text-zinc-500">fee {p.feeSats}</div>
                  </div>
                </div>
              ))}
              {payments.length === 0 ? <div className="text-xs text-zinc-500">No payments yet.</div> : null}
            </div>
          </Card>
        </div>

        <div className="mt-10">
          <Card>
            <div className="flex items-center justify-between">
              <div className="text-sm font-semibold">Meters directory</div>
              <div className="text-xs text-zinc-500">{meters.length} meters</div>
            </div>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full border-separate border-spacing-0 text-sm">
                <thead>
                  <tr className="text-left text-xs font-semibold text-zinc-500">
                    <th className="pb-3">Meter</th>
                    <th className="pb-3">Resource</th>
                    <th className="pb-3">Unit</th>
                    <th className="pb-3">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {meters.map((m) => (
                    <tr key={m.id} className="border-t border-zinc-100">
                      <td className="py-3 font-medium text-zinc-900">{m.name}</td>
                      <td className="py-3 text-zinc-700">{m.resourceType}</td>
                      <td className="py-3 text-zinc-700">{m.unit}</td>
                      <td className="py-3 text-zinc-600">{new Date(m.createdAt).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

