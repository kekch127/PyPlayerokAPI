# -*- coding=utf-8 -*-

from __future__ import annotations

import json
import time
import uuid
import traceback
from threading import Thread, RLock
from queue import Queue
from logging import getLogger
from typing import Callable, Optional

import websocket

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.types.queries import QUERIES
from PyPlayerokAPI.models.chat import Chat, ChatMessage
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from .chat_storage import ChatStorage


class WebSocketClient:

    def __init__(
        self,
        account: AccountClient,
        factory: EventFactory,
        queue: Queue[PlayerokEvent],
        chat_storage: ChatStorage,
        on_possible_new_chat: Optional[Callable[[], None]] = None,
    ):
        self.account = account
        self.factory = factory
        self.queue = queue
        self.chat_storage = chat_storage
        self._on_possible_new_chat = on_possible_new_chat

        self.logger = getLogger(__name__)
        self.ws: Optional[websocket.WebSocket] = None

        self._chat_subscriptions: dict[str, str] = {}
        self._subscribed_chat_ids: set[str] = set()
        self._seen_message_ids: dict[str, str] = {}
        self._send_lock = RLock()
        self._state_lock = RLock()

        self._initialized = False

    def set_on_possible_new_chat(self, callback: Optional[Callable[[], None]]):
        self._on_possible_new_chat = callback

    def start(self):
        Thread(target=self._run, daemon=True).start()

    def subscribe_chat(self, chat_id: str):
        with self._state_lock:
            if chat_id in self._subscribed_chat_ids:
                return
            self._subscribed_chat_ids.add(chat_id)
        if self.ws:
            self._send_chat_message_subscription(chat_id)

    def get_all_ids(self):
        return self.chat_storage.get_all_ids()

    def get(self, chat_id: str):
        return self.chat_storage.get(chat_id)

    def _run(self):
        if not self._initialized:
            self._load_initial_chats()
            self._initialized = True

        while True:
            try:
                self._connect()
                self._receive_loop()
            except websocket._exceptions.WebSocketException:
                time.sleep(3)

    def _load_initial_chats(self):
        try:
            chats = self.account.get_chats(count=24).chats
        except Exception:
            chats = []

        for chat in chats:
            self.chat_storage.upsert(chat)
            self._subscribed_chat_ids.add(chat.id)
            if getattr(chat, "last_message", None) and getattr(chat.last_message, "id", None):
                self._seen_message_ids[chat.id] = chat.last_message.id # type: ignore
            self.queue.put(self.factory.build_chat_initialized_event(chat))

    def _connect(self):
        headers = {
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "no-cache",
            "connection": "Upgrade",
            "origin": "https://playerok.com",
            "pragma": "no-cache",
            "sec-websocket-extensions": "permessage-deflate; client_max_window_bits",
            "cookie": f"token={self.account.token}",
            "user-agent": self.account.user_agent,
        }

        self.logger.info("Connecting...")

        self.ws = websocket.WebSocket(
            sslopt={"ca_certs": self.account.transport._tmp_cert_path}
        )

        self.ws.connect(
            url="wss://ws.playerok.com/graphql",
            header=[f"{k}: {v}" for k, v in headers.items()],
            subprotocols=["graphql-transport-ws"],
        )

        self._send_connection_init()

    def _receive_loop(self):
        while True:
            msg = self.ws.recv() # type: ignore
            Thread(target=self._handle_message, args=(msg,), daemon=True).start()

    def _handle_message(self, raw):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        try:
            if data.get("type") == "connection_ack":
                self._subscribe_chat_updated()
                self._subscribe_user_updated()
                self._resubscribe_chat_messages()
                return

            payload = data.get("payload", {}).get("data", {})

            if "userUpdated" in payload and self._on_possible_new_chat:
                unread_chats = payload.get("userUpdated").get("unreadChatsCounter", 0)
                if unread_chats > 0:
                    self._on_possible_new_chat()

            if "chatUpdated" in payload:
                self._handle_chat_updated(payload["chatUpdated"])

            if "chatMessageCreated" in payload:
                self._handle_chat_message_created(data.get("id"), payload["chatMessageCreated"])

        except Exception:
            self.logger.debug(traceback.format_exc())

    def _handle_chat_updated(self, chat_data):
        chat_obj = Chat.model_validate(chat_data)
        message_data = chat_data.get("lastMessage")
        message_obj = ChatMessage.model_validate(message_data) if message_data else None

        is_new_chat = not self.chat_storage.has(chat_obj.id)
        self.chat_storage.upsert(chat_obj)

        if not self._is_chat_subscribed(chat_obj.id):
            self.subscribe_chat(chat_obj.id)
            if is_new_chat:
                self.queue.put(self.factory.build_chat_initialized_event(chat_obj))

        # некоторые уведомления/системные чаты могут быть доставлены через chatUpdated
        if message_obj and self._is_new_message(chat_obj.id, message_obj.id):
            for event in self.factory.build(message_obj, chat_obj):
                self.queue.put(event)

    def _handle_chat_message_created(self, subscription_id: Optional[str], message_data):
        if not subscription_id:
            return
        with self._state_lock:
            chat_id = self._chat_subscriptions.get(subscription_id)
        if not chat_id:
            return

        chat_obj = self.chat_storage.get(chat_id)
        if not chat_obj:
            try:
                chat_obj = self.account.get_chat(chat_id)
                self.chat_storage.upsert(chat_obj)
            except Exception:
                return

        message_obj = ChatMessage.model_validate(message_data)
        if not self._is_new_message(chat_id, message_obj.id):
            return
        for event in self.factory.build(message_obj, chat_obj):
            self.queue.put(event)

    def _is_chat_subscribed(self, chat_id: str) -> bool:
        with self._state_lock:
            return chat_id in self._subscribed_chat_ids

    def _send_connection_init(self):
        self.ws.send(json.dumps({ # type: ignore
            "type": "connection_init",
            "payload": {
                "x-gql-op": "ws-subscription",
                "x-gql-path": "/self.chats/[id]",
                "x-timezone-offset": -180,
            },
        }))

    def _subscribe_chat_updated(self):
        self._ws_send({
            "id": str(uuid.uuid4()),
            "payload": {
                "extensions": {},
                "operationName": "chatUpdated",
                "query": QUERIES.get("chatUpdated"),
                "variables": {
                    "filter": {"userId": self.account.account_data.id},
                    "showForbiddenImage": True,
                },
            },
            "type": "subscribe",
        })

    def _subscribe_user_updated(self):
        self._ws_send({
            "id": str(uuid.uuid4()),
            "payload": {
                "extensions": {},
                "operationName": "userUpdated",
                "query": QUERIES.get("userUpdated"),
                "variables": {"userId": self.account.account_data.id},
            },
            "type": "subscribe",
        })

    def _resubscribe_chat_messages(self):
        with self._send_lock:
            self._chat_subscriptions = {}

            for chat_id in self.chat_storage.get_all_ids():
                with self._state_lock:
                    self._subscribed_chat_ids.add(chat_id)

            with self._state_lock:
                chat_ids = list(self._subscribed_chat_ids)

            for chat_id in chat_ids:
                self._send_chat_message_subscription(chat_id)

    def _send_chat_message_subscription(self, chat_id: str):
        sub_id = str(uuid.uuid4())
        with self._state_lock:
            self._chat_subscriptions[sub_id] = chat_id
        self._ws_send({
            "id": sub_id,
            "payload": {
                "extensions": {},
                "operationName": "chatMessageCreated",
                "query": QUERIES.get("chatMessageCreated"),
                "variables": {"filter": {"chatId": chat_id}},
            },
            "type": "subscribe",
        })

    def _ws_send(self, payload: dict):
        with self._send_lock:
            if not self.ws:
                return
            self.ws.send(json.dumps(payload))

    def _is_new_message(self, chat_id: str, message_id: Optional[str]) -> bool:
        if not message_id:
            return False
        with self._state_lock:
            last_seen = self._seen_message_ids.get(chat_id)
            if last_seen == message_id:
                return False
            self._seen_message_ids[chat_id] = message_id
            return True
