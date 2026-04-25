from __future__ import annotations

import asyncio
import random
from typing import Callable, Optional

from .store import ConsumptionEvent, Store, now_iso, nid


def _rand(a: float, b: float) -> float:
    return random.random() * (b - a) + a


async def simulation_loop(
    store: Store,
    provider_id: str,
    tick_ms: int,
    on_tick: Optional[Callable[[], None]] = None,
    stop_event: Optional[asyncio.Event] = None,
):
    if stop_event is None:
        stop_event = asyncio.Event()

    while not stop_event.is_set():
        for m in store.meters:
            if m.resourceType == "electricity":
                delta = _rand(0.01, 0.08)
            elif m.resourceType == "gas":
                delta = _rand(0.02, 0.12)
            elif m.resourceType == "hot_water":
                delta = _rand(0.2, 2.5)
            else:
                delta = _rand(0.3, 3.2)

            store.consumption.append(
                ConsumptionEvent(
                    id=nid(),
                    meterId=m.id,
                    ts=now_iso(),
                    delta=float(delta),
                    unit=m.unit,
                )
            )

        # Health mostly healthy
        r = random.random()
        p = next((x for x in store.providers if x.id == provider_id), None)
        if p is not None:
            if r < 0.02:
                p.health = "degraded"
            elif r < 0.025:
                p.health = "down"
            else:
                p.health = "healthy"
            p.updatedAt = now_iso()

        if on_tick is not None:
            on_tick()

        await asyncio.sleep(tick_ms / 1000.0)

