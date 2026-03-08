# -*- coding=utf-8 -*-

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import Optional

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.models.chat import ChatMessage


class MessageResolver:
    """
    Класс для дозагрузки сообщений из API.

    Используется `EventFactory`, когда сообщение, полученное из websocket, не содержит полной информации (например `deal`).
    """
    def __init__(
        self,
        account: AccountClient
    ):
        self._account = account
        self._logger = getLogger(__name__)
    
    
    async def resolve(
        self,
        message_id: str,
        chat_id: str,
        attempts: int = 3,
        delay: float = 6.0
    ) -> Optional[ChatMessage]:
        """
        Пытается получить полную информацию о сообщении.

        Args:
            message_id (str): ID сообщения
            chat_id (str): ID чата
            attempts (int, optional): Количество попыток. Defaults to 3.
            delay (float, optional): Задержка. Defaults to 6.0.

        Returns:
            Optional[ChatMessage]: Сообщение
        """
        for _ in range(attempts):
            await asyncio.sleep(delay)
            
            try:
                msg_list = await self._account.get_chat_messages(chat_id, 12)
            except Exception as e:
                self._logger.exception(f"Не удалось получить сообщения: {e}")
                return None

            try:
                for msg in msg_list.messages or []:
                    if msg.id == message_id:
                        return msg
            except Exception:
                continue
        
        self._logger.debug(f"Не удалось найти сообщение [{message_id}] спусят [{attempts}] попыток")
        return None