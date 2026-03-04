import pytest

from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.dispatcher import EventDispatcher
from PyPlayerokAPI.stream.events.account_event import AccountEvent
from PyPlayerokAPI.models.chat import ChatMessage, Chat
from PyPlayerokAPI.account import AccountClient


@pytest.mark.asyncio
async def test_event_pipeline():

    factory = EventFactory()
    dispatcher = EventDispatcher()

    received = []

    async def handler(account_event):
        received.append(account_event)

    from PyPlayerokAPI.types.enums import EventTypes

    dispatcher.register(EventTypes.NEW_MESSAGE, handler)

    message = ChatMessage(
        id="msg1",
        text="Hello",
        deal=None
    )

    chat = Chat(id="chat1")

    events = await factory.build(message, chat)

    account = AccountClient(token="test")

    for event in events:
        account_event = AccountEvent(account=account, event=event)
        await dispatcher.dispatch(account_event)

    assert len(received) >= 1