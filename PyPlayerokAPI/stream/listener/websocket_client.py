# -*- coding=utf-8 -*-

from __future__ import annotations

import ssl
import asyncio
import json
import uuid
import traceback
from logging import getLogger
from typing import Callable, Optional, List, Dict, Set

import websockets
from websockets.typing import Subprotocol

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.graphql import build_query_payload
from PyPlayerokAPI.models.chat import Chat, ChatMessage
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from .chat_storage import ChatStorage


subprotocols: List[Subprotocol] = [Subprotocol("graphql-transport-ws")]


class WebsocketClient:
    """
    Клиент вебсокета для Playerok
    """
    def __init__(
        self,
        account: AccountClient,
        factory: EventFactory,
        queue: asyncio.Queue[PlayerokEvent],
        chat_storage: ChatStorage,
        on_possible_new_chat: Optional[Callable[[], None]] = None
    ):
        """
        Args:
            account (AccountClient): Клиент аккаунта
            factory (EventFactory): Генератор ивентов
            queue (asyncio.Queue[PlayerokEvent]): Очередь
            chat_storage (ChatStorage): Хранилище чатов
            on_possible_new_chat (Optional[Callable[[], None]], optional): Callback, вызываемый websocket, о возможности появления нового чата. Defaults to None.
        """
        self._account= account
        self._factory = factory
        self._queue = queue
        self._chat_storage = chat_storage
        self._on_possible_new_chat = on_possible_new_chat
        
        self._logger = getLogger(__name__)
        self._ws: Optional[websockets.ClientConnection] = None
        
        self._chat_subscriptions: Dict[str, str] = {}
        self._subscribed_chat_ids: Set[str] = set()
        self._seen_message_ids: Dict[str, str] = {}
        
        self._send_lock = asyncio.Lock()
        self._state_lock = asyncio.Lock()
        self._message_semaphone = asyncio.Semaphore(100)
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    
    async def _run(self):
        await self._load_initial_chats()
        
        while self._running:
            try:
                await self._connect()
                await self._receive_loop()
            except Exception:
                await asyncio.sleep(6)

    # ============== Загрузка ============== #
    async def _load_initial_chats(self):
        """
        Загружает список последних чатов аккаунта через API
        """
        try:
            chats = await asyncio.to_thread(
                self._account.get_chats,
                24
            )
            chats = chats.chats
        except Exception:
            chats = []
        
        for chat in chats:
            await self._chat_storage.upsert(chat)
            self._subscribed_chat_ids.add(chat.id)
            
            if chat.last_message and chat.last_message.id:
                self._seen_message_ids[chat.id] = chat.last_message.id
            
            await self._queue.put(
                self._factory.build_chat_initialized_event(chat)
            )
    
    
    async def _connect(self):
        """
        Устанавливает websocket соединение с сервером Playerok
        """
        headers = {
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "connection": "Upgrade",
            "origin": "https://playerok.com",
            "pragma": "no-cache",
            "sec-websocket-extensions": "permessage-deflate; client_max_window_bits",
            "cookie": f"token={self._account.token}",
            "user-agent": self._account.user_agent,
        }

        self._logger.info("Пытаюсь подключится к Playerok.com...")
        
        ssl_context = ssl.create_default_context(
            cafile = self._account.transport._tmp_cert_path
        )
        
        self._ws = await websockets.connect(
            "wss://ws.playerok.com/graphql",
            additional_headers = headers,
            subprotocols = subprotocols,
            ssl = ssl_context
        )
        
        await self._send_connection_init()
    
    
    async def _receive_loop(self):
        """
        Основной цикл получения websocket сообщений
        """
        if self._ws is None:
            return
        
        async for raw in self._ws:
            async with self._message_semaphone: # защита от перегруза задачами и блокировки loop
                asyncio.create_task(self._handle_message(raw))
    
    # ============== Обработка ============== #
    async def _handle_message(
        self,
        raw
    ):
        """
        Обрабатывает сырое сообщение websocket

        Args:
            raw (str): JSON сообщение, полученные из websocket
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return
        
        self._logger.debug(f"Получена и загружена raw из WS -> {data}")
        
        try:
            if data.get("type") == "connection_ack":
                await self._subscribe_chat_updated()
                await self._subscribe_user_updated()
                await self._resubscribe_chat_messages()
                return
            
            payload = data.get("payload", {}).get("data", {})
            
            if "userUpdated" in payload and self._on_possible_new_chat:
                unread_chats = payload["userUpdated"].get("unreadChatsCounter", 0)
                if unread_chats > 0:
                    self._on_possible_new_chat()
            
            if "chatUpdated" in payload:
                await self._handle_chat_updated(
                    chat_data = payload["chatUpdated"]
                )
            
            if "chatMessageCreated" in payload:
                await self._handle_chat_message_created(
                    subscription_id = data.get("id"),
                    message_data = payload["chatMessageCreated"]
                )
        except Exception as e:
            self._logger.exception(f"Не удалось обработать запрос из WS: {e}")
            self._logger.debug(traceback.format_exc())
    
    
    async def _handle_chat_updated(
        self,
        chat_data: Dict
    ):
        """
        Обрабатывает ивент обновления чата

        Args:
            chat_data (Dict): Данные чата из websocket
        """
        chat_obj = Chat.model_validate(chat_data)
        message_data = chat_data.get("lastMessage")
        message_obj = ChatMessage.model_validate(message_data) if message_data else None
        
        is_new_chat = not await self._chat_storage.has(chat_obj.id)
        await self._chat_storage.upsert(chat_obj)
        
        if is_new_chat:
            await self._queue.put(
                self._factory.build_chat_initialized_event(chat_obj)
            )
        
        if not await self._is_chat_subscribed(chat_obj.id):
            await self._subscribe_chat(chat_obj.id)
            # TODO: получить ивент и обработать с чата
        
        if message_obj and self._is_new_message(chat_obj.id, message_obj.id):
            events = await self._factory.build(message_obj, chat_obj)
            
            for event in events:
                await self._queue.put(event)
    
    
    async def _handle_chat_message_created(
        self,
        subscription_id: Optional[str],
        message_data: Dict
    ):
        """
        Обрабатывает ивент создания нового чата

        Args:
            subscription_id (Optional[str]): ID подписки websocket
            message_data (Dict): Данные чата
        """
        if not subscription_id:
            return
        
        async with self._state_lock:
            chat_id = self._chat_subscriptions.get(subscription_id)
        
        if not chat_id:
            return
        
        chat_obj = await self._chat_storage.get(chat_id)
        if not chat_obj:
            try:
                chat_obj = await asyncio.to_thread(
                    self._account.get_chat,
                    chat_id
                )
                await self._chat_storage.upsert(chat_obj)
            except:
                return
        
        message_obj = ChatMessage.model_validate(message_data)
        
        if not self._is_new_message(chat_id, message_obj.id):
            return
        
        events = await self._factory.build(message_obj, chat_obj)
        
        for event in events:
            await self._queue.put(event)
    
    # ============== Подписки ============== #
    async def _ws_send(
        self,
        payload: Dict
    ):
        async with self._send_lock:
            if not self._ws:
                return
            await self._ws.send(json.dumps(payload))
    
    
    async def _send_connection_init(self):
        await self._ws_send({
            "type": "connection_init",
            "payload": {
                "x-gql-op": "ws-subscription",
                "x-gql-path": "/self.chats/[id]",
                "x-timezone-offset": -180,
            },
        })
    
    
    async def _subscribe_chat_updated(self):
        query_payload = build_query_payload(
            operation_name = "chatUpdated",
            query_key = "chatUpdated",
            variables = {
                "filter": {
                    "userId": self._account.account_data.id
                },
                "showForbiddenImage": True,
            }
        )
        
        await self._ws_send({
            "id": str(uuid.uuid4()),
            "payload": {
                "extensions": {},
                **query_payload,
            },
            "type": "subscribe",
        })
    
    
    async def _subscribe_user_updated(self):
        query_payload = build_query_payload(
            operation_name = "userUpdated",
            query_key = "userUpdated",
            variables = {
                "userId": self._account.account_data.id
            }
        )
        
        await self._ws_send({
            "id": str(uuid.uuid4()),
            "payload": {
                "extensions": {},
                **query_payload,
            },
            "type": "subscribe",
        })
    
    
    async def _send_chat_message_subscription(
        self,
        chat_id: str
    ):
        sub_id = str(uuid.uuid4())
        
        async with self._state_lock:
            self._chat_subscriptions[sub_id] = chat_id
        
        query_payload = build_query_payload(
            operation_name = "chatMessageCreated",
            query_key = "chatMessageCreated",
            variables = {
                "filter": {
                    "chatId": chat_id
                },
            }
        )
        
        await self._ws_send({
            "id": sub_id,
            "payload": {
                "extensions": {},
                **query_payload,
            },
            "type": "subscribe",
        })
    
    
    async def _resubscribe_chat_messages(self):
        async with self._send_lock:
            self._chat_subscriptions = {}
            
            for chat_id in await self._chat_storage.get_all_ids():
                async with self._state_lock:
                    self._subscribed_chat_ids.add(chat_id)
            
            async with self._state_lock:
                chat_ids = list(self._subscribed_chat_ids)
            
            for chat_id in chat_ids:
                await self._send_chat_message_subscription(chat_id)
    
    # ============== Утилиты ============== #
    def _is_new_message(
        self,
        chat_id: str,
        message_id: Optional[str]
    ) -> bool:
        if not message_id:
            return False
        
        last_seen = self._seen_message_ids.get(chat_id)
        if last_seen == message_id:
            return False
        
        self._seen_message_ids[chat_id] = message_id
        return True
    
    
    async def _is_chat_subscribed(
        self,
        chat_id: str
    ) -> bool:
        async with self._state_lock:
            return chat_id in self._subscribed_chat_ids
    
    
    async def _subscribe_chat(
        self,
        chat_id: str
    ):
        async with self._state_lock:
            if chat_id in self._subscribed_chat_ids:
                return
            
            self._subscribed_chat_ids.add(chat_id)
        
        if self._ws:
            await self._send_chat_message_subscription(chat_id)
    
    
    def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run())
    
    async def stop(self):
        self._running = False
        
        if self._ws:
            await self._ws.close()
        
        if self._task:
            await self._task