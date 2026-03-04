# -*- coding=utf-8 -*-

import asyncio
from logging import getLogger
from typing import Dict, Optional

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from .chat_storage import ChatStorage


class ReviewWatcher:
    """
    Листенер за отзывами по сделкам.
    
    Отслеживает сделки, помеченные `EventFactory`.
    
    После обнаружения отзыва:
        - создает ивент `NEW_REVIEW`
        - отправляет в очередь
    """
    def __init__(
        self,
        account: AccountClient,
        factory: EventFactory,
        queue: asyncio.Queue[PlayerokEvent],
        chat_storage: ChatStorage
    ):
        """
        Args:
            account (AccountClient): Клиент аккаунта
            factory (EventFactory): Генератор ивентов
            queue (asyncio.Queue[PlayerokEvent]): Очередь
            chat_storage (ChatStorage): Хранилище чатов
        """
        self._account = account
        self._factory = factory
        self._queue = queue
        self._chat_storage = chat_storage

        self._review_deal_times: Dict[str, Dict[str, float]] = {}
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._logger = getLogger(__name__)

    async def _should_check_review_deal(
        self,
        deal_id: str,
        delay: int = 30,
        max_tries: int = 30
    ) -> bool:

        now = asyncio.get_event_loop().time()
        info = self._review_deal_times.get(deal_id, {"last": 0, "tries": 0})

        if now - info["last"] > delay:
            self._review_deal_times[deal_id] = {
                "last": now,
                "tries": info["tries"] + 1
            }
            return True

        if info["tries"] >= max_tries:
            await self._factory.unmark_review_check(deal_id)
            self._review_deal_times.pop(deal_id, None)

        return False

    async def _run(self):
        while self._running:

            for deal_id in await self._factory.get_review_check_deals():
                try:
                    if not await self._should_check_review_deal(deal_id):
                        continue

                    # Оборачиваем в asyncio.to_thread по той причине, что get_deal синхронная
                    deal = await asyncio.to_thread(self._account.get_deal, deal_id)
                    if not deal or not deal.review:
                        continue

                    await self._factory.unmark_review_check(deal_id)
                    self._review_deal_times.pop(deal_id, None)

                    chat_obj = None

                    if getattr(deal, "chat", None):
                        chat_obj = await self._chat_storage.get(deal.chat.id) # type: ignore
                        if not chat_obj:
                            try:
                                # Оборачиваем в asyncio.to_thread по той причине, что get_chat синхронная
                                chat_obj = await asyncio.to_thread(self._account.get_chat, deal.chat.id) # type: ignore
                            except Exception:
                                chat_obj = deal.chat

                        deal.chat = chat_obj

                    event = self._factory.build_review_event(deal, chat=chat_obj)

                    await self._queue.put(event)

                except Exception as e:
                    self._logger.exception(f"Не удалось получить отзыв: {e}")

            await asyncio.sleep(1)

    def start(self):
        if self._task:
            return
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._running = False
        
        if self._task:
            await self._task
            self._task = None