import pytest
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from PyPlayerokAPI.types.enums import EventTypes
from PyPlayerokAPI.models.chat import ChatMessage, Chat
from PyPlayerokAPI.models.item import ItemDeal


class DummyDeal:
    id = "deal123"


@pytest.mark.asyncio
async def test_build_new_message_event():
    factory = EventFactory()

    message = ChatMessage(
        id="msg1",
        text="Hello",
        deal=None
    )

    chat = Chat(id="chat1")

    events = await factory.build(message, chat)

    assert len(events) == 1
    assert events[0].type == EventTypes.NEW_MESSAGE


@pytest.mark.asyncio
async def test_mark_processed():
    factory = EventFactory()

    assert factory.mark_processed("deal1") is True
    assert factory.mark_processed("deal1") is False


@pytest.mark.asyncio
async def test_review_marking():
    factory = EventFactory()

    factory.mark_review_check("deal1")
    deals = factory.get_review_check_deals()

    assert "deal1" in deals

    factory.unmark_review_check("deal1")

    assert "deal1" not in factory.get_review_check_deals()