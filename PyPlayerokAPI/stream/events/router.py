# -*- coding=utf-8 -*-

from __future__ import annotations

from PyPlayerokAPI.types.enums import EventTypes
from .dispatcher import EventDispatcher, HandlerType


class PlayerokRouter:
    def __init__(
        self,
        dispatcher: EventDispatcher
    ):
        self._dispatcher = dispatcher
    
    
    def on(self, event_type: EventTypes):
        def decorator(func: HandlerType):
            self._dispatcher.register(event_type, func)
            return func
        return decorator
    
    
    def on_chat_initialized(self):
        return self.on(EventTypes.CHAT_INITIALIZED)

    def on_new_message(self):
        return self.on(EventTypes.NEW_MESSAGE)

    def on_new_deal(self):
        return self.on(EventTypes.NEW_DEAL)

    def on_new_review(self):
        return self.on(EventTypes.NEW_REVIEW)

    def on_deal_confirmed(self):
        return self.on(EventTypes.DEAL_CONFIRMED)

    def on_deal_confirmed_automatically(self):
        return self.on(EventTypes.DEAL_CONFIRMED_AUTOMATICALLY)

    def on_deal_rolled_back(self):
        return self.on(EventTypes.DEAL_ROLLED_BACK)

    def on_deal_has_problem(self):
        return self.on(EventTypes.DEAL_HAS_PROBLEM)

    def on_deal_problem_resolved(self):
        return self.on(EventTypes.DEAL_PROBLEM_RESOLVED)

    def on_deal_status_changed(self):
        return self.on(EventTypes.DEAL_STATUS_CHANGED)

    def on_item_paid(self):
        return self.on(EventTypes.ITEM_PAID)

    def on_item_sent(self):
        return self.on(EventTypes.ITEM_SENT)