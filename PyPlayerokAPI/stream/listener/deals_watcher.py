# -*- coding=utf-8 -*-

from __future__ import annotations

import asyncio
import traceback
# from datetime import datetime
from logging import getLogger
from typing import Dict, List, Optional

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from PyPlayerokAPI.types.enums import ChatTypes
# from PyPlayerokAPI.models import Chat, ItemDeal
from .chat_storage import ChatStorage


class DealWatcher:
    """
    Листенер за изменениями сделок.
    
    Периодически проверяет чаты аккаунта и отслеживает изменения статуса сделок.
    
    При обнаружении изменений:
        - формирует ивент через `EventFactory`
        - помещает в очередь ивентов
    """
    def __init__(
        self,
        account: AccountClient,
        factory: EventFactory,
        queue: asyncio.Queue[PlayerokEvent],
        chat_storage: ChatStorage,
        websocket = None,
    ):
        """
        Args:
            account (AccountClient): Клиент аккаунта
            factory (EventFactory): Генератор ивентов
            queue (asyncio.Queue[PlayerokEvent]): Очередь
            chat_storage (ChatStorage): Хранилище чатов
            websocket (_type_, optional): Клиент. Defaults to None.
        """
        self._account = account
        self._factory = factory
        self._queue = queue
        self._chat_storage = chat_storage
        self._websocket = websocket

        self._possible_new_chat = asyncio.Event()
        self._active_deals: Dict[str, List[tuple]] = {}

        self._task: Optional[asyncio.Task] = None
        self._status_task: Optional[asyncio.Task] = None
        self._running = False
        self._logger = getLogger(__name__)


    def set_websocket(self, websocket):
        self._websocket = websocket


    def notify_possible_new_chat(self):
        self._possible_new_chat.set()


    # def _parse_dt(self, raw_dt: str | None) -> datetime:
    #     if not raw_dt:
    #         return datetime.utcnow()
    #     try:
    #         return datetime.fromisoformat(raw_dt)
    #     except ValueError:
    #         return datetime.fromisoformat(raw_dt.replace("Z", "+00:00"))

    # async def _account_call(self, func, *args):
    #     return await asyncio.to_thread(func, *args)


    # def _set_active_deal(
    #     self,
    #     chat: Chat,
    #     deal: ItemDeal,
    #     status_date: datetime
    # ):
    #     if chat.id not in self._active_deals:
    #         self._active_deals[chat.id] = []
        
    #     try:
    #         deal_tuple = [dtuple for dtuple in self._active_deals[chat.id] if deal.id in dtuple][0]
    #     except:
    #         deal_tuple = ()
        
    #     if not deal_tuple:
    #         self._active_deals[chat.id].append((deal.id, deal.status, status_date))
    #     else:
    #         indx = self._active_deals[chat.id].index(deal_tuple)
    #         self._active_deals[chat.id][indx] = (deal.id, deal.status, status_date)


    # async def _listen_deal_statuses(self):
    #     while self._running:
    #         for chat_id, deals in list(self._active_deals.items()):
    #             messages = []
                
    #             try:
    #                 for _ in range(3):
    #                     try:
    #                         msg_list = await self._account_call(
    #                             self._account.get_chat_messages,
    #                             chat_id,
    #                             24
    #                         )

    #                         messages = sorted(
    #                             msg_list.messages or [],
    #                             key=lambda x: self._parse_dt(x.created_at)
    #                         )
    #                         break
    #                     except Exception as e:
    #                         await asyncio.sleep(4)
                    
    #                 for deal_id, last_status, status_date in deals:
    #                     try:
    #                         status_msgs = [
    #                             msg for msg in messages
    #                             if msg.deal and getattr(msg.deal, "status", None) and self._parse_dt(msg.created_at) >= status_date
    #                         ]
                            
    #                         for msg in status_msgs:
    #                             msg_date = self._parse_dt(msg.created_at)
    #                             if msg.deal.status == last_status and msg_date == status_date:
    #                                 continue
                                
    #                             try:
    #                                 chat = await self._account_call(
    #                                     self._account.get_chat,
    #                                     chat_id
    #                                 )
    #                             except:
    #                                 chat = None
                                    
    #                             if not chat:
    #                                 continue
                                
    #                             events = await asyncio.to_thread(self._factory.build, msg, chat)
    #                             for event in events:
    #                                 await self._queue.put(event)

    #                             # if msg.deal:
    #                             #     self._set_active_deal(chat, msg.deal, msg_date)
    #                     except Exception as e:
    #                         self._logger.debug(f"Ошибка проверки статусов в сделке {deal_id}: {traceback.format_exc()}")

    #             except Exception as e:
    #                 self._logger.debug(f"Ошибка проверки статусов {e}")

    #         await asyncio.sleep(5)


    async def _run(self):
        while self._running:
            try:
                await self._possible_new_chat.wait()
                self._possible_new_chat.clear()

                # Контроль частоты запросов
                delay = 10 - (asyncio.get_event_loop().time() - self._last_chat_check)
                if delay > 0:
                    await asyncio.sleep(delay)

                self._last_chat_check = asyncio.get_event_loop().time()

                known_chat_ids = set(await self._chat_storage.get_all_ids())

                chat_list = None

                # Повторные попытки
                for _ in range(3):
                    try:
                        chat_list = await self._account.get_chats(5, ChatTypes.PM)
                    except Exception:
                        await asyncio.sleep(4)
                        continue

                    new_deal_exists = any(
                        chat_.last_message
                        and chat_.last_message.text == "{{ITEM_PAID}}"
                        for chat_ in chat_list.chats
                    )

                    if new_deal_exists:
                        break

                    await asyncio.sleep(4)

                if not chat_list:
                    continue

                for chat_ in chat_list.chats:
                    if chat_.id in known_chat_ids:
                        continue

                    last_message = chat_.last_message
                    if not last_message:
                        continue

                    if last_message.text == "{{ITEM_PAID}}":

                        await self._chat_storage.upsert(chat_)

                        if self._websocket:
                            self._websocket._subscribe_chat(chat_.id)

                        # if last_message.deal:
                        #     status_date = self._parse_dt(last_message.created_at)
                            # self._set_active_deal(chat_, last_message.deal, status_date)

                        await self._queue.put(
                            self._factory.build_chat_initialized_event(chat_)
                        )

                        events = await self._factory.build(last_message, chat_)

                        for event in events:
                            await self._queue.put(event)

            except Exception as e:
                self._logger.exception(f"Ошибка получения данных: {e}")
                self._logger.debug(traceback.format_exc())
    
    
    def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run())
        # self._status_task = asyncio.create_task(self._listen_deal_statuses())

    async def stop(self):
        self._running = False
        
        if self._task:
            await self._task

        if self._status_task:
            await self._status_task