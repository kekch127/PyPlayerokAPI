from __future__ import annotations

import asyncio
from threading import Thread, Event as ThreadEvent
from typing import Iterable, Optional, Union
from queue import Queue

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream.events.async_dispatcher import AsyncEventDispatcher
from PyPlayerokAPI.stream.events.async_router import AsyncPlayerokRouter
from PyPlayerokAPI.stream.events.account_event import AccountEvent
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.markers import register_default_markers
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from PyPlayerokAPI.stream.listener.chat_storage import ChatStorage
from PyPlayerokAPI.stream.listener.message_resolver import MessageResolver
from PyPlayerokAPI.stream.listener.websocket_client import WebSocketClient
from PyPlayerokAPI.stream.listener.review_watcher import ReviewWatcher
from PyPlayerokAPI.stream.listener.deals_watcher import DealWatcher


class AsyncPlayerokListener:
    def __init__(
        self,
        account: AccountClient,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        queue: Optional[asyncio.Queue[Union[PlayerokEvent, AccountEvent]]] = None,
        include_account: bool = False,
        queue_maxsize: int = 0,
    ):
        self._account = account
        self._loop = loop
        self._queue: asyncio.Queue[Union[PlayerokEvent, AccountEvent]] = queue or asyncio.Queue(maxsize=queue_maxsize)
        self._include_account = include_account

        self.dispatcher = AsyncEventDispatcher(loop=self._loop)
        self.router = AsyncPlayerokRouter(self.dispatcher)

        self._sync_queue: Queue[Optional[PlayerokEvent]] = Queue()
        self._chat_storage = ChatStorage()
        self._factory = EventFactory()
        register_default_markers(self._factory)

        resolver = MessageResolver(account)
        self._factory.set_message_resolver(resolver.resolve)

        self._deal_watcher = DealWatcher(
            account,
            self._factory,
            self._sync_queue, # type: ignore
            chat_storage = self._chat_storage,
        )

        self._websocket = WebSocketClient(
            account,
            self._factory,
            self._sync_queue, # type: ignore
            chat_storage = self._chat_storage,
            on_possible_new_chat = self._deal_watcher.notify_possible_new_chat,
        )
        self._deal_watcher.set_websocket(self._websocket)

        self._review_watcher = ReviewWatcher(
            account,
            self._factory,
            self._sync_queue, # type: ignore
            chat_storage=self._chat_storage,
        )

        self._stop_event = ThreadEvent()
        self._thread: Optional[Thread] = None
        self._dispatch_task: Optional[asyncio.Task[None]] = None
        self._started = False

    @property
    def queue(self) -> asyncio.Queue[Union[PlayerokEvent, AccountEvent]]:
        return self._queue

    def start(self, *, dispatch: bool = True):
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        elif not self._loop.is_running():
            raise RuntimeError(
                "AsyncPlayerokListener.start() requires a running asyncio loop"
            )

        self.dispatcher.set_loop(self._loop)

        if not self._started:
            self._websocket.start()
            self._review_watcher.start()
            self._deal_watcher.start()
            self._started = True

        if not self._thread or not self._thread.is_alive():
            self._thread = Thread(target=self._forward_loop, daemon=True)
            self._thread.start()

        if dispatch and (self._dispatch_task is None or self._dispatch_task.done()):
            if not self._loop or not self._loop.is_running():
                raise RuntimeError(
                    "AsyncPlayerokListener.start(dispatch = True) must be called inside a running asyncio loop"
                )
            self._dispatch_task = self._loop.create_task(self._dispatch_loop())

    def stop(self):
        self._stop_event.set()
        self._sync_queue.put(None)
        if self._dispatch_task and not self._dispatch_task.done():
            self._dispatch_task.cancel()

    async def get(self) -> Union[PlayerokEvent, AccountEvent]:
        return await self._queue.get()

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.get()

    def _forward_loop(self):
        while True:
            event = self._sync_queue.get()
            if event is None or self._stop_event.is_set():
                break

            item = AccountEvent(account=self._account, event=event) if self._include_account else event

            if self._loop is None:
                return

            self._loop.call_soon_threadsafe(self._put_nowait, item)

    def _put_nowait(self, item: Union[PlayerokEvent, AccountEvent]):
        try:
            self._queue.put_nowait(item)
        except asyncio.QueueFull:
            pass

    async def _dispatch_loop(self):
        while True:
            item = await self._queue.get()
            if isinstance(item, AccountEvent):
                await self.dispatcher.dispatch(item)
            else:
                await self.dispatcher.dispatch(AccountEvent(account=self._account, event=item))


class AsyncMultiAccountListener:
    def __init__(
        self,
        accounts: Iterable[AccountClient],
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        queue_maxsize: int = 0,
    ):
        self._loop = loop
        self._queue: asyncio.Queue[Union[PlayerokEvent, AccountEvent]] = asyncio.Queue(maxsize=queue_maxsize)
        self.dispatcher = AsyncEventDispatcher(loop=self._loop)
        self.router = AsyncPlayerokRouter(self.dispatcher)
        self._dispatch_task: Optional[asyncio.Task[None]] = None
        self._listeners = [
            AsyncPlayerokListener(
                account=acc,
                loop=self._loop,
                queue=self._queue,
                include_account=True,
            )
            for acc in accounts
        ]

    @property
    def listeners(self) -> list[AsyncPlayerokListener]:
        return self._listeners

    @property
    def queue(self) -> asyncio.Queue[Union[PlayerokEvent, AccountEvent]]:
        return self._queue

    def start(self, *, dispatch: bool = True):
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        elif not self._loop.is_running():
            raise RuntimeError(
                "AsyncMultiAccountListener.start() requires a running asyncio loop"
            )

        self.dispatcher.set_loop(self._loop)

        for listener in self._listeners:
            listener._loop = self._loop
            listener.start(dispatch=False)

        if dispatch and (self._dispatch_task is None or self._dispatch_task.done()):
            if not self._loop or not self._loop.is_running():
                raise RuntimeError(
                    "AsyncMultiAccountListener.start(dispatch = True) must be called inside a running asyncio loop"
                )
            self._dispatch_task = self._loop.create_task(self._dispatch_loop())

    async def get(self) -> AccountEvent:
        item = await self._queue.get()
        if isinstance(item, AccountEvent):
            return item
        raise TypeError("AsyncMultiAccountListener queue contains non-account event item")

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self.get()

    async def _dispatch_loop(self):
        while True:
            item = await self._queue.get()
            if isinstance(item, AccountEvent):
                await self.dispatcher.dispatch(item)

    def stop(self):
        for listener in self._listeners:
            listener.stop()
        if self._dispatch_task and not self._dispatch_task.done():
            self._dispatch_task.cancel()
