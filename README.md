# AI Consumption Payment (Lightning)

Full-stack demo: real-time utility consumption → tariff calculation → automatic micro-settlement over Bitcoin Lightning.

The UI is intentionally styled like [`402index.io`](https://402index.io/) (stats cards, protocol tabs, directory tables, health badges).

## Problem & goal (Hack-Nation Challenge 2)

In Germany, many tenants pay **Warmmiete** (rent + estimated utilities) and only receive a true-up invoice once per year. This project demonstrates a more transparent alternative:

- **Smart-meter-like ingestion** of electricity/gas/hot-water/cold-water usage
- **Deterministic tariffing** (auditable rules, not “AI math”)
- **Automatic micro-settlement** over **Bitcoin Lightning** (push payments)
- **Live UI** that makes consumption and payments visible in real time

## What runs today

This repo includes a **Python FastAPI** server that serves:

- **Frontend**: `GET /` (HTML + Tailwind CDN + JS polling)
- **Backend API**: `GET /v1/*` (meters, providers, stats, payments, ledger)
- **Simulation**: meter events + auto-settlement loop (mock Lightning) on an interval
- **Authentication**: user register/login with an httpOnly session cookie (SQLite-backed)
- **User dashboard**: live spend + tariff price variation + carbon agent portfolio
- **Warmmiete budget agent**: compares the user’s prepaid utilities budget (27% of Warmmiete, accrued to-date) vs actual consumption cost and shows **SURPLUS/DEFICIT**
- **Notifications**: warns the user when they are exceeding the prepaid utilities budget

## Architecture

### High-level components

```mermaid
flowchart LR
  A[Smart meters / Meter gateway (simulated)] -->|consumption events| API[Backend API]

  subgraph BACKEND["Backend API (FastAPI)"]
    B1[Consumption store]
    B2[Tariff engine (EUR cost)]
    B3[Settlement policy (threshold/time)]
    B4[Ledger + payments log]
    B5[Lightning client (mock now, LND/CLN later)]
  end

  API -->|JSON /v1/*| C[Frontend UI (402index-like)]
  B5 -->|invoice + pay| D[Utility provider wallet/node (mocked in MVP)]
  B4 -->|audit trail| C
```

### “Pay-as-you-go” settlement flow (Lightning push payments)

```mermaid
sequenceDiagram
  autonumber
  participant M as Meter (simulated)
  participant API as Backend (FastAPI)
  participant T as Tariff Engine
  participant S as Settlement Policy
  participant LN as Lightning Client (mock)
  participant P as Provider (demo)

  M->>API: POST/append consumption event (delta, ts)
  API->>T: compute cost in EUR (+VAT)
  T-->>API: cost_eur
  API->>API: add ledger entry + increment unsettled(EUR)
  API->>S: check threshold (e.g. €0.10)
  alt threshold met
    S->>LN: create invoice(amount_sats)
    LN-->>S: invoice
    S->>LN: pay invoice
    LN-->>S: settled (payment_hash, preimage, fee)
    S->>API: append Payment + fee ledger entry
  else below threshold
    S-->>API: do nothing yet
  end
  API-->>API: expose updated state via /v1/*
```

### Data model (what gets recorded)

```mermaid
erDiagram
  METER ||--o{ CONSUMPTION_EVENT : emits
  METER }o--|| TARIFF : priced_by
  CONSUMPTION_EVENT ||--o{ LEDGER_ENTRY : produces
  PROVIDER ||--o{ PAYMENT : receives

  METER {
    string id
    string name
    string resourceType
    string unit
    string createdAt
  }

  TARIFF {
    string id
    string resourceType
    string currency
    float pricePerUnit
    float vatRate
    string updatedAt
  }

  CONSUMPTION_EVENT {
    string id
    string meterId
    string ts
    float delta
    string unit
  }

  LEDGER_ENTRY {
    string id
    string ts
    string meterId
    string resourceType
    float amountEur
    int amountSats
    string reason
  }

  PROVIDER {
    string id
    string name
    string protocol
    string health
    string updatedAt
  }

  PAYMENT {
    string id
    string ts
    string providerId
    int amountSats
    int feeSats
    string status
    string paymentHash
    string preimage
    string memo
  }
```

## Local dev (recommended)

Prereqs: Python 3.8+

```bash
cp .env.example .env
python3 -m pip install -r requirements.txt
python3 -m uvicorn server.app:app --reload --port 4000
```

Open:

- App: `http://localhost:4000/`
- Health: `http://localhost:4000/health`
- Stats: `http://localhost:4000/v1/stats`

## Configuration

The app reads environment variables (see `.env.example`):

- **`PORT`**: server port (default `4000`)
- **`SIMULATION_ENABLED`**: generate meter events automatically (`true|false`)
- **`SIMULATION_TICK_MS`**: simulator tick interval (e.g. `1500`)
- **`SETTLEMENT_THRESHOLD_EUR`**: trigger payment once unsettled EUR ≥ threshold (e.g. `0.10`)
- **`BTC_EUR_RATE`**: fixed conversion rate for demo (e.g. `60000`)

## API (MVP)

Base path: `/v1`

- **`GET /v1/stats`**: homepage KPIs + provider health summary + unsettled EUR
- **`GET /v1/providers`**: providers list (health, protocol)
- **`GET /v1/meters`**: meters directory
- **`GET /v1/tariffs`**: tariffs (EUR pricing rules)
- **`GET /v1/consumption?limit=200`**: recent consumption events
- **`GET /v1/ledger?limit=200`**: audit ledger entries
- **`GET /v1/payments?limit=200`**: payment history (mock Lightning)
- **`POST /v1/ingest`**: ingest a consumption event

### Auth & dashboard

Pages:

- **`GET /login`**: login/register page
- **`GET /dashboard`**: authenticated dashboard (live spend + charts)

Auth endpoints:

- **`POST /auth/register`**: `{ email, password }` → sets `acp_session` cookie
- **`POST /auth/login`**: `{ email, password }` → sets `acp_session` cookie
- **`POST /auth/logout`**: clears cookie
- **`GET /v1/me`**: returns current user (requires cookie)

User endpoints:

- **`GET /v1/me/summary`**: totals by resource + recent Lightning settlements
- **`GET /v1/me/tariffs/history?resourceType=...`**: tariff history for the “price variation” chart
- **`GET /v1/me/profile`**: Warmmiete settings (monthly EUR + 73/27 split)
- **`PUT /v1/me/profile`**: update Warmmiete settings
- **`GET /v1/me/notifications`**: in-app notifications (e.g. deficit warnings)

### Warmmiete budget model (Germany)

We model the common idea that monthly Warmmiete contains:

- **73% rent** (fixed)
- **27% utilities** (electricity/gas/water)

The app computes a **utilities budget-to-date** within the current month:

\[
\text{utilitiesBudgetToDate} = \text{WarmmieteMonthly} \cdot 0.27 \cdot \frac{\text{dayOfMonth}}{\text{daysInMonth}}
\]

Then compares it to the **actual utilities cost-to-date** derived from the ledger (deterministic tariffing).

- If **budget − actual > 0** → **SURPLUS** (eligible to invest via carbon agent)
- If **budget − actual < 0** → **DEFICIT** (creates a warning notification)

### Carbon agent (sats-settled trading)

This is a demo “agent policy” that reacts to **savings vs a baseline**:

- **If consumption is lower than baseline (surplus)**: invest part of the surplus into **buying carbon credits**
- **If consumption is higher than baseline (deficit)**: **sell credits** first; if still short, take a capped **debt**

Important: **trades are settled in Bitcoin (sats)**. Carbon prices are still displayed in **EUR/tonne** for readability.

Endpoints (requires auth):

- **`GET /v1/me/carbon/portfolio`**: carbon position (tonnes), debt (**sats**), and current carbon price
- **`GET /v1/me/carbon/trades?limit=...`**: recent carbon trades (each includes `notionalSats`)
- **`GET /v1/me/carbon/price?limit=...`**: carbon price series (EUR/tonne) for charting

Example:

```bash
curl -s http://localhost:4000/v1/stats
curl -s http://localhost:4000/v1/payments
```

## Lightning integration status

Today the Lightning layer is **mocked** (`server/lightning_mock.py`) so the demo works locally without a node.

To move from mock → real Lightning:

- **LND**: generate invoice via `lnrpc` (gRPC / REST) and pay via `SendPaymentV2`
- **Core Lightning**: generate invoice via `invoice` and pay via `pay`

The code is structured so the Lightning client can be swapped without changing the settlement policy and ledger.

## Notes

- The `apps/*` Node scaffold is optional
