import pytest
import asyncio

from PyPlayerokAPI.stream.events.event_factory import EventFactory


@pytest.mark.asyncio
async def test_processed_ttl_cleanup():

    factory = EventFactory(processed_ttl=1)

    assert factory.mark_processed("deal1") is True
    assert factory.mark_processed("deal1") is False

    await asyncio.sleep(1.1)

    factory._cleanup_processed()

    assert factory.mark_processed("deal1") is True