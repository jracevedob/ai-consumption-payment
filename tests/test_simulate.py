import asyncio

import pytest

from server.simulate import simulation_loop
from server.store import default_store


@pytest.mark.asyncio
async def test_simulation_loop_appends_consumption_and_updates_health():
    s = default_store()
    pid = s.providers[0].id
    stop = asyncio.Event()

    # Stop after a short delay
    async def stopper():
        await asyncio.sleep(0.05)
        stop.set()

    asyncio.create_task(stopper())
    await simulation_loop(store=s, provider_id=pid, tick_ms=10, on_tick=None, stop_event=stop)

    assert len(s.consumption) >= len(s.meters)
    assert s.providers[0].health in ("healthy", "degraded", "down", "unknown")

