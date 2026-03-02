# -*- coding=utf-8 -*-

import time
import traceback
from threading import Thread
from logging import getLogger
from queue import Queue

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from .chat_storage import ChatStorage


class ReviewWatcher:

    def __init__(
        self,
        account: AccountClient,
        factory: EventFactory,
        queue: Queue[PlayerokEvent],
        chat_storage: ChatStorage,
    ):
        self._account = account
        self._factory = factory
        self._queue = queue
        self._chat_storage = chat_storage

        self._deal_checks = {}
        self._logger = getLogger(__name__)

    def start(self):
        Thread(target=self._run, daemon=True).start()

    def _should_check_deal(self, deal_id, delay=30, max_tries=30):
        now = time.time()
        info = self._deal_checks.get(deal_id, {"last": 0, "tries": 0})

        if now - info["last"] > delay:
            self._deal_checks[deal_id] = {
                "last": now,
                "tries": info["tries"] + 1,
            }
            return True

        if info["tries"] >= max_tries:
            self._factory.unmark_review_check(deal_id)
            self._deal_checks.pop(deal_id, None)

        return False

    def _run(self):
        while True:
            for deal_id in list(self._factory.review_check_deals):
                try:
                    if not self._should_check_deal(deal_id):
                        continue

                    deal = self._account.get_deal(deal_id)
                    if not deal or not deal.review:
                        continue

                    self._factory.unmark_review_check(deal_id)

                    chat_obj = None
                    if getattr(deal, "chat", None):
                        try:
                            chat_obj = self._chat_storage.get(deal.chat.id) # type: ignore
                        except Exception:
                            chat_obj = None

                        if chat_obj is None:
                            try:
                                chat_obj = self._account.get_chat(deal.chat.id) # type: ignore
                            except Exception:
                                chat_obj = deal.chat

                        deal.chat = chat_obj

                    event = self._factory.build_review_event(deal, chat=chat_obj)
                    self._queue.put(event)

                except Exception:
                    self._logger.debug(traceback.format_exc())

            time.sleep(1)
