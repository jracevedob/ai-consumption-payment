const toneClass = (h) => {
  if (h === "healthy") return "bg-emerald-50 text-emerald-700 ring-emerald-200";
  if (h === "degraded") return "bg-amber-50 text-amber-700 ring-amber-200";
  if (h === "down") return "bg-rose-50 text-rose-700 ring-rose-200";
  return "bg-zinc-50 text-zinc-700 ring-zinc-200";
};

const fmt = (n) => (typeof n === "number" ? n.toLocaleString() : "—");

async function api(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`API ${path} failed`);
  return await res.json();
}

function pill(text, tone) {
  const span = document.createElement("span");
  span.className = `inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ring-1 ${toneClass(tone)}`;
  span.textContent = text;
  return span;
}

function clear(el) {
  while (el.firstChild) el.removeChild(el.firstChild);
}

async function refresh() {
  const [stats, providers, meters, payments] = await Promise.all([
    api("/v1/stats"),
    api("/v1/providers"),
    api("/v1/meters"),
    api("/v1/payments")
  ]);

  document.getElementById("kpi-endpoints").textContent = fmt(stats.endpointsIndexed);
  document.getElementById("kpi-verified").textContent = fmt(stats.paymentVerified);
  document.getElementById("kpi-providers").textContent = fmt(stats.providersIndexed);
  document.getElementById("kpi-healthy").textContent = fmt(stats.healthy);
  document.getElementById("last-checked").textContent = `Last checked: ${new Date(stats.lastCheckedAt).toLocaleString()}`;
  document.getElementById("unsettled").textContent = `€${Number(stats.unsettledEur || 0).toFixed(2)}`;

  const pbody = document.getElementById("providers-tbody");
  clear(pbody);
  for (const p of providers) {
    const tr = document.createElement("tr");
    tr.className = "border-t border-zinc-100";

    const tdName = document.createElement("td");
    tdName.className = "py-3 font-medium text-zinc-900";
    tdName.textContent = p.name;

    const tdProto = document.createElement("td");
    tdProto.className = "py-3 text-zinc-700";
    tdProto.textContent = p.protocol;

    const tdHealth = document.createElement("td");
    tdHealth.className = "py-3";
    tdHealth.appendChild(pill(p.health, p.health));

    const tdUpd = document.createElement("td");
    tdUpd.className = "py-3 text-zinc-600";
    tdUpd.textContent = new Date(p.updatedAt).toLocaleTimeString();

    tr.append(tdName, tdProto, tdHealth, tdUpd);
    pbody.appendChild(tr);
  }

  document.getElementById("meters-count").textContent = `${meters.length} meters`;
  const mbody = document.getElementById("meters-tbody");
  clear(mbody);
  for (const m of meters) {
    const tr = document.createElement("tr");
    tr.className = "border-t border-zinc-100";

    const tdA = document.createElement("td");
    tdA.className = "py-3 font-medium text-zinc-900";
    tdA.textContent = m.name;

    const tdB = document.createElement("td");
    tdB.className = "py-3 text-zinc-700";
    tdB.textContent = m.resourceType;

    const tdC = document.createElement("td");
    tdC.className = "py-3 text-zinc-700";
    tdC.textContent = m.unit;

    const tdD = document.createElement("td");
    tdD.className = "py-3 text-zinc-600";
    tdD.textContent = new Date(m.createdAt).toLocaleDateString();

    tr.append(tdA, tdB, tdC, tdD);
    mbody.appendChild(tr);
  }

  const payEl = document.getElementById("payments");
  clear(payEl);
  const last = payments.slice(-5).reverse();
  if (last.length === 0) {
    const d = document.createElement("div");
    d.className = "text-xs text-zinc-500";
    d.textContent = "No payments yet.";
    payEl.appendChild(d);
  } else {
    for (const p of last) {
      const row = document.createElement("div");
      row.className = "flex items-center justify-between gap-3 rounded-xl border border-zinc-200 p-3";

      const left = document.createElement("div");
      left.className = "min-w-0";
      const h = document.createElement("div");
      h.className = "truncate text-xs font-medium text-zinc-900";
      h.textContent = p.paymentHash;
      const t = document.createElement("div");
      t.className = "text-xs text-zinc-500";
      t.textContent = new Date(p.ts).toLocaleTimeString();
      left.append(h, t);

      const right = document.createElement("div");
      right.className = "text-right";
      const a = document.createElement("div");
      a.className = "text-xs font-semibold text-zinc-900";
      a.textContent = `${p.amountSats} sats`;
      const f = document.createElement("div");
      f.className = "text-xs text-zinc-500";
      f.textContent = `fee ${p.feeSats}`;
      right.append(a, f);

      row.append(left, right);
      payEl.appendChild(row);
    }
  }
}

refresh().catch(() => {});
setInterval(() => refresh().catch(() => {}), 1500);

