from PyPlayerokAPI.stream.events.router import PlayerokRouter
from PyPlayerokAPI.stream.events.dispatcher import EventDispatcher
from PyPlayerokAPI.types.enums import EventTypes


def test_router_register():

    dispatcher = EventDispatcher()
    router = PlayerokRouter(dispatcher)

    async def handler(account_event):
        pass

    router.on(EventTypes.NEW_MESSAGE)(handler)

    assert EventTypes.NEW_MESSAGE in dispatcher._handlers
    assert len(dispatcher._handlers[EventTypes.NEW_MESSAGE]) == 1