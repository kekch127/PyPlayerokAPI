# -*- coding=utf-8 -*-

from __future__ import annotations

import time
from logging import getLogger
from typing import Optional

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.models.chat import ChatMessage


class MessageResolver:
    def __init__(self, account: AccountClient):
        self._account = account
        self._logger = getLogger(__name__)

    def resolve(
        self,
        message_id: str,
        chat_id: str,
        attempts: int = 3,
        delay: float = 4.0,
    ) -> Optional[ChatMessage]:
        for _ in range(attempts):
            time.sleep(delay)
            try:
                msg_list = self._account.get_chat_messages(chat_id, count=12)
            except Exception:
                return None

            try:
                for msg in msg_list.messages or []:
                    if msg.id == message_id:
                        return msg
            except Exception:
                continue

        self._logger.debug("Message not found after retries")
        return None
