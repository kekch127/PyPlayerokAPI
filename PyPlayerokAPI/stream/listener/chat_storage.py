# -*- coding=utf-8 -*-

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional

from PyPlayerokAPI.models.chat import Chat


class ChatStorage:
    """
    In-memory хранилище чатов.
    
    Используется слушателями (`DealWatcher`, `ReviewWatcher`, `WebsocketClient`)
    для быстрого доступа к уже известным чатам без повторных запросов к API.

    Хранилище потокобезопасно для asyncio
    """
    def __init__(self):
        self._chats: Dict[str, Chat] = {} # str - ID чата
        self._lock: asyncio.Lock = asyncio.Lock()

    async def upsert(self, chat: Chat) -> None:
        """
        Добавляет или обновляет чат

        Args:
            chat (Chat): Чат
        """
        async with self._lock:
            self._chats[chat.id] = chat

    async def get(self, chat_id: str) -> Optional[Chat]:
        """
        Возвращает чат по ID

        Args:
            chat_id (str): ID чата

        Returns:
            Optional[Chat]: Чат
        """
        async with self._lock:
            return self._chats.get(chat_id)

    async def has(self, chat_id: str) -> bool:
        """
        Проверяет, есть ли чат

        Args:
            chat_id (str): ID чата

        Returns:
            bool
        """
        async with self._lock:
            return chat_id in self._chats

    async def get_all(self) -> List[Chat]:
        """
        Возвращает список всех сохраненных чатов

        Returns:
            List[Chat]: 
        """
        async with self._lock:
            return list(self._chats.values())

    async def get_all_ids(self) -> List[str]:
        """
        Возвращает список ID всех чатов

        Returns:
            List[str]: 
        """
        async with self._lock:
            return list(self._chats.keys())