# -*- coding=utf-8 -*-

from __future__ import annotations

import asyncio
from time import time
from typing import Callable, Awaitable, Dict, List, Optional, Set
from logging import getLogger

from PyPlayerokAPI.models.chat import Chat, ChatMessage
from PyPlayerokAPI.models.item import ItemDeal
from PyPlayerokAPI.types.enums import EventTypes
from .event_wrapper import PlayerokEvent
from .markers.registry import MarkerRegistry


# resolver(message_id, chat_id) -> ChatMessage | None (lazy enrichment)
# по сути нужно для ДОзагрузки сообщения через id сообщения и чата
MessageResolver = Callable[[str, str], Awaitable[Optional[ChatMessage]]] 


class EventFactory:
    """
    Конструктор ивентов `PlayerokEvent` по маркерам из `ChatMessage`.
    
    Логика работы:
        1. Получает сообщение
        2. Проверяет на наличие маркера
        3. При необходимости ДОзагружает данные (конкретно `deal` (сделку))
        4. Генерирует список событий `PlayerokEvent`
        5. Управляет вспомогательными состояниями
    """
    def __init__(
        self,
        message_resolver: Optional[MessageResolver] = None,
        registry: Optional[MarkerRegistry] = None,
        processed_ttl: int = 3600
    ):
        self._registry = registry or MarkerRegistry()
        self._message_resolver = message_resolver
        
        self._review_check_deals: Set[str] = set() # сделки, по которым необходимо проверить отзыв 
        self._processed_deals: Dict[str, float] = {} # сделки, которые уже были обработаны (по сути своеобразный фильтр от дубликатов)
        
        self._PROCESSED_TTL = processed_ttl
        self._lock: asyncio.Lock = asyncio.Lock()
        self._logger = getLogger(__name__)
    
    
    def set_message_resolver(
        self,
        resolver: Optional[MessageResolver]
    ):
        """
        Устанавливает функцию дозагрузки сообщений.

        Args:
            resolver (Optional[MessageResolver]): Функция-загрузчик
        """
        self._message_resolver = resolver
    
    
    async def build(
        self,
        message: ChatMessage,
        chat: Chat
    ) -> List[PlayerokEvent]:
        """    
        Создает список `PlayerokEvent` из сообщений по маркеру.
        
        Главная точка входа для генерации ивентов. Отвечает за общий pipeline обработки сообщений. 
        
        Схема работы:
            ChatMessage -> EventFactory.build() -> MarkerRegistry -> BaseMarker.build() -> List[PlayerokEvent]

        Args:
            message (ChatMessage): Сообщение
            chat (Chat): Чат, к которому относится сообщение

        Returns:
            List[PlayerokEvent]: Список ивентов
        """
        await self._cleanup_processed()
        
        if not message: 
            return []
        
        # Дополнительная проверка на пустое сообщение
        if not isinstance(message.text, str) or not message.text:
            return [
                PlayerokEvent(
                    type = EventTypes.NEW_MESSAGE,
                    chat = chat,
                    message = message
                )
            ]
        
        clean_message_text = message.text.strip()
        
        marker = self._registry.get(clean_message_text)
        if not marker:
            return [
                PlayerokEvent(
                    type = EventTypes.NEW_MESSAGE,
                    chat = chat,
                    message = message
                )
            ]
        
        resolved = await self._resolve_message_if_needed(message, chat)
        events = await marker.build(self, resolved, chat)
        
        if not events and not getattr(resolved, "deal", None):
            return [
                PlayerokEvent(
                    type = EventTypes.NEW_MESSAGE,
                    chat = chat,
                    message = message
                )
            ]
        
        return events
    
    
    async def mark_review_check(
        self,
        deal_id: str
    ):
        """
        Добавляет ID сделки в список сделок, требующих проверки отзыва.

        Args:
            deal_id (str): ID сделки
        """
        async with self._lock:
            self._review_check_deals.add(deal_id)
    
    
    async def unmark_review_check(
        self,
        deal_id: str
    ):
        """
        Удаляет ID сделки из списка, требующих проверки отзыва.

        Args:
            deal_id (str): ID сделки
        """
        async with self._lock:
            self._review_check_deals.discard(deal_id)
    
    
    async def mark_processed(
        self,
        deal_id: str
    ) -> bool:
        """
        Проверяет, обрабатывалась ли эта сделка.

        Args:
            deal_id (str): ID сделки

        Returns:
            bool: `False` - в случае, если обрабатывалась, иначе `True` (и добавляет в список обработанных сделок)
        """
        now = time()
        
        async with self._lock:
            ts = self._processed_deals.get(deal_id)
            if ts and (now - ts) < self._PROCESSED_TTL:
                return False
            
            self._processed_deals[deal_id] = now
            return True
    
    # ============== Билдеры простых ивентов ============== #
    def build_review_event(
        self,
        deal: ItemDeal,
        chat: Optional[Chat] = None
    ) -> PlayerokEvent:
        return PlayerokEvent(
            type = EventTypes.NEW_REVIEW, 
            chat = chat, 
            deal = deal
        )
    
    def build_chat_initialized_event(
        self,
        chat: Chat
    ) -> PlayerokEvent:
        return PlayerokEvent(
            type = EventTypes.CHAT_INITIALIZED,
            chat = chat
        )
    
    
    # ============== Помощники ============== #
    async def _cleanup_processed(self):
        """
        Функция очистки списка сделок, которые уже были обработаны
        """
        now = time()
        
        async with self._lock:
            expired = [
                deal_id
                for deal_id, ts in self._processed_deals.items()
                if (now - ts) > self._PROCESSED_TTL
            ]
            
            for deal_id in expired:
                del self._processed_deals[deal_id]

    
    # Решает проблему гонки потоков в review_watcher при чтении _review_check_deals
    async def get_review_check_deals(self) -> List[str]:
        async with self._lock:
            return list(self._review_check_deals)
    
    
    async def _resolve_message_if_needed(
        self,
        message: ChatMessage,
        chat: Chat
    ) -> ChatMessage:
        """
        Функция ДОзагрузки информации сообщения (`deal`) из чата.

        Args:
            message (ChatMessage): Сообщение
            chat (Chat): Чат, к которому относится сообщение

        Returns:
            ChatMessage: Сообщение со сделкой
        """
        if not self._message_resolver:
            return message
        
        # Если уже содержит deal - не нужно ДОзагружать
        if getattr(message, "deal", None):
            return message
        
        # Если нет необходимых идентификаторов чата - не сможем загрузить
        if not message.id or not chat or not chat.id:
            return message
        
        try:
            resolved = await self._message_resolver(message.id, chat.id)
            
            return resolved or message
        except Exception as e:
            self._logger.exception(f"Не удалось дозагрузить информацию с `deal` из сообщений: {e}")
            return message