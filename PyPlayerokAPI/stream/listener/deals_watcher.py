# -*- coding=utf-8 -*-

import time
import traceback
from threading import Thread, Event
from logging import getLogger
from queue import Queue

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from PyPlayerokAPI.types.enums import ChatTypes
from .chat_storage import ChatStorage


class DealWatcher:

    def __init__(
        self,
        account: AccountClient,
        factory: EventFactory,
        queue: Queue[PlayerokEvent],
        chat_storage: ChatStorage,
        websocket=None,
    ):
        self._account = account
        self._factory = factory
        self._queue = queue
        self._chat_storage = chat_storage
        self._websocket = websocket

        self._possible_new_chat = Event()
        self._last_chat_check = 0
        self._logger = getLogger(__name__)

    def set_websocket(self, websocket):
        self._websocket = websocket

    def notify_possible_new_chat(self):
        self._possible_new_chat.set()

    def start(self):
        Thread(target=self._run, daemon=True).start()

    def _wait_for_check_new_chats(self, delay=10):
        sleep_time = delay - (time.time() - self._last_chat_check)
        if sleep_time > 0:
            time.sleep(sleep_time)

    def _run(self):
        while True:
            try:
                self._possible_new_chat.wait()
                self._wait_for_check_new_chats()
                self._last_chat_check = time.time()
                self._possible_new_chat.clear()

                known_chat_ids = set(self._chat_storage.get_all_ids())

                chat_list = None
                for _ in range(3):
                    try:
                        chat_list = self._account.get_chats(
                            count=3,
                            type=ChatTypes.PM,
                        )
                    except Exception:
                        time.sleep(4)
                        continue

                    new_deal_exists = any(
                        chat_.last_message and chat_.last_message.text == "{{ITEM_PAID}}"
                        for chat_ in chat_list.chats
                    )

                    if new_deal_exists:
                        break

                    time.sleep(4)

                if not chat_list:
                    continue

                for chat_ in chat_list.chats:
                    if chat_.id in known_chat_ids:
                        continue

                    last_message = chat_.last_message
                    if last_message and last_message.text == "{{ITEM_PAID}}":
                        self._chat_storage.upsert(chat_)
                        if self._websocket:
                            self._websocket.subscribe_chat(chat_.id)

                        self._queue.put(self._factory.build_chat_initialized_event(chat_))

                        events = self._factory.build(last_message, chat_)
                        for event in events:
                            self._queue.put(event)

            except Exception:
                self._logger.debug(traceback.format_exc())
