# -*- coding=utf-8 -*-

from __future__ import annotations

from abc import ABC
from typing import List, TYPE_CHECKING
from PyPlayerokAPI.models.chat import Chat, ChatMessage
from PyPlayerokAPI.types.enums import EventTypes
from ..event_wrapper import PlayerokEvent

if TYPE_CHECKING:
    from ..event_factory import EventFactory


class BaseMarker(ABC):
    """
    Базовый класс для всех системных маркеров.

    Каждый маркер:
        - имеет строковый идентификатор (marker)
        - умеет строить список PlayerokEvent
    """

    marker: str
    event_type: EventTypes
    include_status_change: bool = True
    deduplicate: bool = False
    review_check: bool = False

    async def build(
        self,
        factory: "EventFactory",
        message: ChatMessage,
        chat: Chat,
    ) -> List[PlayerokEvent]:
        """
        Создает маркер

        Args:
            factory (EventFactory): Конструктор
            message (ChatMessage): Сообщение
            chat (Chat): Чат, к которому относится сообщение

        Returns:
            List[PlayerokEvent]: Список ивентов
        """
        deal = message.deal
        if not deal:
            return []

        if self.review_check:
            await factory.mark_review_check(deal.id)

        if self.deduplicate and not factory.mark_processed(deal.id):
            return []

        events = [
            PlayerokEvent(
                type = self.event_type,
                chat = chat,
                deal = deal,
                message = message,
            )
        ]

        if self.include_status_change:
            events.append(
                PlayerokEvent(
                    type = EventTypes.DEAL_STATUS_CHANGED,
                    chat = chat,
                    deal = deal,
                    message = message,
                )
            )

        return events