# -*- coding=utf-8 -*-

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Protocol, Set
from threading import RLock
from logging import getLogger

from PyPlayerokAPI.models.chat import Chat, ChatMessage
from PyPlayerokAPI.models.item import ItemDeal
from PyPlayerokAPI.types.enums import EventTypes
from .event_wrapper import PlayerokEvent

MessageResolver = Callable[[str, str], Optional[ChatMessage]]


class MarkerHandler(Protocol):
    def __call__(self, factory: "EventFactory", message: ChatMessage, chat: Chat) -> List[PlayerokEvent]:
        ...


class EventFactory:

    def __init__(self, message_resolver: Optional[MessageResolver] = None):
        self._markers: Dict[str, MarkerHandler] = {}
        self._message_resolver = message_resolver
        self._lock = RLock()
        self._logger = getLogger(__name__)

        self.review_check_deals: Set[str] = set()
        self.processed_deals: Set[str] = set()

    def register_marker(self, marker: str, builder: MarkerHandler):
        self._markers[marker] = builder

    def set_message_resolver(self, resolver: Optional[MessageResolver]):
        self._message_resolver = resolver

    def build(self, message: ChatMessage, chat: Chat) -> List[PlayerokEvent]:
        if not message:
            return []

        handler = self._markers.get(message.text) # type: ignore
        if handler:
            resolved = self._resolve_message_if_needed(message, chat)
            events = handler(self, resolved, chat)
            if not events and not getattr(resolved, "deal", None):
                return [PlayerokEvent(type=EventTypes.NEW_MESSAGE, chat=chat, message=message)]
            return events

        return [PlayerokEvent(type=EventTypes.NEW_MESSAGE, chat=chat, message=message)]

    def build_review_event(self, deal: ItemDeal, chat: Optional[Chat] = None) -> PlayerokEvent:
        return PlayerokEvent(type=EventTypes.NEW_REVIEW, chat=chat, deal=deal)

    def build_chat_initialized_event(self, chat: Chat) -> PlayerokEvent:
        return PlayerokEvent(type=EventTypes.CHAT_INITIALIZED, chat=chat)

    def mark_review_check(self, deal_id: str):
        with self._lock:
            self.review_check_deals.add(deal_id)

    def unmark_review_check(self, deal_id: str):
        with self._lock:
            self.review_check_deals.discard(deal_id)

    def mark_processed(self, deal_id: str) -> bool:
        with self._lock:
            if deal_id in self.processed_deals:
                return False
            self.processed_deals.add(deal_id)
            return True

    def _resolve_message_if_needed(self, message: ChatMessage, chat: Chat) -> ChatMessage:
        if not self._message_resolver:
            return message
        if getattr(message, "deal", None):
            return message
        if not message.id or not chat or not chat.id:
            return message
        try:
            resolved = self._message_resolver(message.id, chat.id)
            return resolved or message
        except Exception:
            self._logger.debug("Failed to resolve message with deal data")
            return message
