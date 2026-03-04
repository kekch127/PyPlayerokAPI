import pytest

from PyPlayerokAPI.stream.events.dispatcher import EventDispatcher
from PyPlayerokAPI.stream.events.account_event import AccountEvent
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from PyPlayerokAPI.types.enums import EventTypes
from PyPlayerokAPI.account import AccountClient


@pytest.mark.asyncio
async def test_dispatch_split_handler():

    dispatcher = EventDispatcher()

    received = []

    async def handler(account, event):
        received.append(event)

    dispatcher.register(EventTypes.NEW_MESSAGE, handler)

    account = AccountClient(token="test_token")

    event = PlayerokEvent(type=EventTypes.NEW_MESSAGE)

    account_event = AccountEvent(
        account=account,
        event=event
    )

    await dispatcher.dispatch(account_event)

    assert len(received) == 1