from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .lightning_mock import MockLightning
from .settlement import wire_tick
from .simulate import simulation_loop
from .store import ConsumptionEvent, Store, default_store, now_iso


load_dotenv()

PORT = int(os.getenv("PORT", "4000"))
SIMULATION_ENABLED = os.getenv("SIMULATION_ENABLED", "true").lower() == "true"
SIMULATION_TICK_MS = int(os.getenv("SIMULATION_TICK_MS", "1500"))
SETTLEMENT_THRESHOLD_EUR = float(os.getenv("SETTLEMENT_THRESHOLD_EUR", "0.10"))
BTC_EUR_RATE = float(os.getenv("BTC_EUR_RATE", "60000"))

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="AI Consumption Payment API", version="0.1.0")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

store: Store = default_store()
lightning = MockLightning()
provider_id = store.providers[0].id

stop_event = asyncio.Event()


@app.on_event("startup")
async def _startup():
    if not SIMULATION_ENABLED:
        return
    on_tick = wire_tick(
        store=store,
        provider_id=provider_id,
        btc_eur_rate=BTC_EUR_RATE,
        threshold_eur=SETTLEMENT_THRESHOLD_EUR,
        lightning=lightning,
    )
    asyncio.create_task(
        simulation_loop(
            store=store,
            provider_id=provider_id,
            tick_ms=SIMULATION_TICK_MS,
            on_tick=on_tick,
            stop_event=stop_event,
        )
    )


@app.on_event("shutdown")
async def _shutdown():
    stop_event.set()


@app.get("/", response_class=HTMLResponse)
async def home(req: Request):
    return templates.TemplateResponse("index.html", {"request": req})


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/v1/stats")
async def stats() -> Dict[str, Any]:
    counts = {"healthy": 0, "degraded": 0, "down": 0, "unknown": 0}
    for p in store.providers:
        counts[p.health] += 1

    endpoints_indexed = len(store.meters) * 4
    payment_verified = len([p for p in store.payments if p.status == "settled"])

    return {
        "endpointsIndexed": endpoints_indexed,
        "paymentVerified": payment_verified,
        "providersIndexed": len(store.providers),
        "providersVerified": len([p for p in store.providers if p.protocol != "mock"]),
        **counts,
        "lastCheckedAt": now_iso(),
        "unsettledEur": float(store.unsettledEurByProviderId.get(provider_id, 0.0)),
    }


@app.get("/v1/providers")
async def providers():
    return store.providers


@app.get("/v1/meters")
async def meters():
    return store.meters


@app.get("/v1/tariffs")
async def tariffs():
    return store.tariffs


@app.get("/v1/consumption")
async def consumption(limit: int = 200):
    return store.consumption[-limit:]


@app.get("/v1/ledger")
async def ledger(limit: int = 200):
    return store.ledger[-limit:]


@app.get("/v1/payments")
async def payments(limit: int = 200):
    return store.payments[-limit:]


@app.post("/v1/ingest")
async def ingest(payload: Dict[str, Any]):
    meter_id = payload.get("meterId")
    delta = payload.get("delta")
    ts = payload.get("ts") or now_iso()

    m = next((x for x in store.meters if x.id == meter_id), None)
    if m is None:
        raise HTTPException(status_code=404, detail="meter not found")
    if not isinstance(delta, (int, float)):
        raise HTTPException(status_code=400, detail="delta must be number")

    ev = ConsumptionEvent(id="manual", meterId=meter_id, ts=ts, delta=float(delta), unit=m.unit)
    store.consumption.append(ev)
    return {"ok": True, "event": ev}


def run_dev():
    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=PORT, reload=True)

