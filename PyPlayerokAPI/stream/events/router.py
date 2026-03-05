# -*- coding=utf-8 -*-

from __future__ import annotations

from typing import Optional
from PyPlayerokAPI.types.enums import EventTypes
from .dispatcher import EventDispatcher, HandlerType


class PlayerokRouter:
    def __init__(
        self,
        dispatcher: EventDispatcher
    ):
        self._dispatcher = dispatcher
    
    
    def on(
        self,
        event_type: EventTypes,
        marker: Optional[str] = None
    ):
        def decorator(func: HandlerType):
            async def wrapper(account, event):
                event_marker = getattr(event, "marker", None)
                
                # если обработчик без marker — принимаем только обычные события
                if marker is None:
                    if event_marker is not None:
                        return
                # если обработчик с marker — проверяем совпадение
                else:
                    if event_marker != marker:
                        return
                
                result = func(account, event) # type: ignore
                
                if result:
                    if hasattr(result, "__await__"):
                        await result
            
            self._dispatcher.register(event_type, wrapper)
            
            return func
        return decorator
    
    
    def on_chat_initialized(self):
        return self.on(EventTypes.CHAT_INITIALIZED)

    def on_new_message(self, marker: Optional[str] = None):
        return self.on(EventTypes.NEW_MESSAGE, marker)

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