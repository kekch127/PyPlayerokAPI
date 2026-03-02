# -*- coding=utf-8 -*-

from __future__ import annotations

from threading import RLock
from typing import Dict, List, Optional

from PyPlayerokAPI.models.chat import Chat


class ChatStorage:
    def __init__(self):
        self._chats: Dict[str, Chat] = {}
        self._lock = RLock()

    def upsert(self, chat: Chat):
        with self._lock:
            self._chats[chat.id] = chat

    def get(self, chat_id: str) -> Optional[Chat]:
        with self._lock:
            return self._chats.get(chat_id)

    def has(self, chat_id: str) -> bool:
        with self._lock:
            return chat_id in self._chats

    def get_all(self) -> List[Chat]:
        with self._lock:
            return list(self._chats.values())

    def get_all_ids(self) -> List[str]:
        with self._lock:
            return list(self._chats.keys())
