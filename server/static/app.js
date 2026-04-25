function applyTheme(theme) {
  const root = document.documentElement;
  const isDark =
    theme === "dark" || (theme !== "light" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);

  root.classList.toggle("dark", isDark);
  try {
    localStorage.setItem("theme", isDark ? "dark" : "light");
  } catch {}

  const icon = document.getElementById("theme-icon");
  const label = document.getElementById("theme-label");
  if (icon) icon.textContent = isDark ? "☀" : "☾";
  if (label) label.textContent = isDark ? "Light" : "Dark";
}

function initThemeToggle() {
  let saved = "system";
  try {
    saved = localStorage.getItem("theme") || "system";
  } catch {}
  applyTheme(saved);

  const btn = document.getElementById("theme-toggle");
  if (!btn) return;
  btn.addEventListener("click", () => {
    const isDark = document.documentElement.classList.contains("dark");
    applyTheme(isDark ? "light" : "dark");
  });
}

const toneClass = (h) => {
  if (h === "healthy") return "bg-emerald-50 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-200 dark:ring-emerald-900";
  if (h === "degraded") return "bg-amber-50 text-amber-700 ring-amber-200 dark:bg-amber-950/40 dark:text-amber-200 dark:ring-amber-900";
  if (h === "down") return "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-rose-950/40 dark:text-rose-200 dark:ring-rose-900";
  return "bg-zinc-50 text-zinc-700 ring-zinc-200 dark:bg-zinc-900 dark:text-zinc-200 dark:ring-zinc-800";
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
    tr.className = "border-t border-zinc-100 dark:border-zinc-900";

    const tdName = document.createElement("td");
    tdName.className = "py-3 font-medium text-zinc-900 dark:text-zinc-50";
    tdName.textContent = p.name;

    const tdProto = document.createElement("td");
    tdProto.className = "py-3 text-zinc-700 dark:text-zinc-300";
    tdProto.textContent = p.protocol;

    const tdHealth = document.createElement("td");
    tdHealth.className = "py-3";
    tdHealth.appendChild(pill(p.health, p.health));

    const tdUpd = document.createElement("td");
    tdUpd.className = "py-3 text-zinc-600 dark:text-zinc-400";
    tdUpd.textContent = new Date(p.updatedAt).toLocaleTimeString();

    tr.append(tdName, tdProto, tdHealth, tdUpd);
    pbody.appendChild(tr);
  }

  document.getElementById("meters-count").textContent = `${meters.length} meters`;
  const mbody = document.getElementById("meters-tbody");
  clear(mbody);
  for (const m of meters) {
    const tr = document.createElement("tr");
    tr.className = "border-t border-zinc-100 dark:border-zinc-900";

    const tdA = document.createElement("td");
    tdA.className = "py-3 font-medium text-zinc-900 dark:text-zinc-50";
    tdA.textContent = m.name;

    const tdB = document.createElement("td");
    tdB.className = "py-3 text-zinc-700 dark:text-zinc-300";
    tdB.textContent = m.resourceType;

    const tdC = document.createElement("td");
    tdC.className = "py-3 text-zinc-700 dark:text-zinc-300";
    tdC.textContent = m.unit;

    const tdD = document.createElement("td");
    tdD.className = "py-3 text-zinc-600 dark:text-zinc-400";
    tdD.textContent = new Date(m.createdAt).toLocaleDateString();

    tr.append(tdA, tdB, tdC, tdD);
    mbody.appendChild(tr);
  }

  const payEl = document.getElementById("payments");
  clear(payEl);
  const last = payments.slice(-5).reverse();
  if (last.length === 0) {
    const d = document.createElement("div");
    d.className = "text-xs text-zinc-500 dark:text-zinc-400";
    d.textContent = "No payments yet.";
    payEl.appendChild(d);
  } else {
    for (const p of last) {
      const row = document.createElement("div");
      row.className =
        "flex items-center justify-between gap-3 rounded-xl border border-zinc-200 p-3 dark:border-zinc-800 dark:bg-zinc-950";

      const left = document.createElement("div");
      left.className = "min-w-0";
      const h = document.createElement("div");
      h.className = "truncate text-xs font-medium text-zinc-900 dark:text-zinc-50";
      h.textContent = p.paymentHash;
      const t = document.createElement("div");
      t.className = "text-xs text-zinc-500 dark:text-zinc-400";
      t.textContent = new Date(p.ts).toLocaleTimeString();
      left.append(h, t);

      const right = document.createElement("div");
      right.className = "text-right";
      const a = document.createElement("div");
      a.className = "text-xs font-semibold text-zinc-900 dark:text-zinc-50";
      a.textContent = `${p.amountSats} sats`;
      const f = document.createElement("div");
      f.className = "text-xs text-zinc-500 dark:text-zinc-400";
      f.textContent = `fee ${p.feeSats}`;
      right.append(a, f);

      row.append(left, right);
      payEl.appendChild(row);
    }
  }
}

initThemeToggle();
refresh().catch(() => {});
setInterval(() => refresh().catch(() => {}), 1500);

