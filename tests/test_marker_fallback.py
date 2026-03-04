import pytest

from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.models.chat import ChatMessage, Chat
from PyPlayerokAPI.types.enums import EventTypes


@pytest.mark.asyncio
async def test_unknown_marker_fallback():

    factory = EventFactory()

    message = ChatMessage(
        id="1",
        text="UNKNOWN_MARKER_TEXT",
        deal=None
    )

    chat = Chat(id="chat1")

    events = await factory.build(message, chat)

    assert events[0].type == EventTypes.NEW_MESSAGE