# -*- coding=utf-8 -*-

from __future__ import annotations

import asyncio
from typing import Optional, Union, Self, Iterable, List

from PyPlayerokAPI.account import AccountClient
from PyPlayerokAPI.stream.events.dispatcher import EventDispatcher
from PyPlayerokAPI.stream.events.router import PlayerokRouter
from PyPlayerokAPI.stream.events.account_event import AccountEvent
from PyPlayerokAPI.stream.events.event_factory import EventFactory
from PyPlayerokAPI.stream.events.event_wrapper import PlayerokEvent
from PyPlayerokAPI.stream.listener.chat_storage import ChatStorage
from PyPlayerokAPI.stream.listener.message_resolver import MessageResolver
from PyPlayerokAPI.stream.listener.websocket_client import WebsocketClient
from PyPlayerokAPI.stream.listener.review_watcher import ReviewWatcher
from PyPlayerokAPI.stream.listener.deals_watcher import DealWatcher


class PlayerokAccountListener:
    """
    Инициализирует слушаеть событий для аккаунта Playerok.
    """
    def __init__(
        self,
        account: AccountClient,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        queue: Optional[asyncio.Queue[Union[PlayerokEvent, AccountEvent]]] = None,
        include_account: bool = False,
        queue_maxsize: int = 0,
        processed_ttl: int = 3600,
    ):
        """
        Args:
            account (AccountClient): Клиент аккаунта 
            loop (Optional[asyncio.AbstractEventLoop], optional): Asyncio event loop в котором будет работать listener. Defaults to None.
            queue (Optional[asyncio.Queue[Union[PlayerokEvent, AccountEvent]]], optional): Внешняя очередь событий (если нужна своя). Defaults to None.
            include_account (bool, optional): Если `True` - оборачивает события в `AccountEvent`. Defaults to False.
            queue_maxsize (int, optional): Максимальный размер публичной очереди. Defaults to 0.
            processed_ttl (int, optional): TTL для защиты от повторной обработки сделок и очистки памяти. Defaults to 3600.
        """
        self._account = account
        self._loop = loop
        self._include_account = include_account
        
        # Создаем 2 разные очереди для соответствия типов + правильного хендла событий для конкретного аккаунта
        # Итоговый поток данных выглядит так:
        # WebsocketClient -> DealWatcher -> ReviewWatcher -> AnyWatcher(custom) -> Queue[PlayerokEvent] -> _forward_loop -> Queue[PlayerokEvent, AccountEvent] -> Dispatcher
        
        # отдельная очередь для глобального листенера который преобразует PlayerokEvent в AccountEvent, чтобы связать ивент с аккаунтом 
        # (по сути это listenerAPI)
        self._public_queue: asyncio.Queue[Union[PlayerokEvent, AccountEvent]] = (
            queue or asyncio.Queue(maxsize = queue_maxsize)
        )
        # Внутреняя очередь, в которую все вотчеры записывают ивенты
        # (это для Watchers)
        self._internal_queue: asyncio.Queue[PlayerokEvent] = asyncio.Queue() 
        
        self._dispatcher = EventDispatcher(loop = self._loop)
        self._router = PlayerokRouter(dispatcher = self._dispatcher)
        
        self._chat_storage = ChatStorage()
        self._factory = EventFactory(processed_ttl = processed_ttl)
        
        resolver = MessageResolver(account = self._account)
        self._factory.set_message_resolver(resolver.resolve)
        
        self._dispatch_task: Optional[asyncio.Task] = None
        self._forward_task: Optional[asyncio.Task] = None
        self._started = False
        
        self._deal_watcher = DealWatcher(
            account = self._account,
            factory = self._factory,
            queue = self._internal_queue,
            chat_storage = self._chat_storage,
        )
        
        self._websocket = WebsocketClient(
            account = self._account,
            factory = self._factory,
            queue = self._internal_queue,
            chat_storage = self._chat_storage,
            on_possible_new_chat = self._deal_watcher.notify_possible_new_chat,
        )
        self._deal_watcher.set_websocket(self._websocket)
        
        self._review_watcher = ReviewWatcher(
            account = self._account,
            factory = self._factory,
            queue = self._internal_queue,
            chat_storage = self._chat_storage,
        )


    @property
    def queue(self) -> asyncio.Queue[Union[PlayerokEvent, AccountEvent]]:
        """
        Возвращает публичную очередь ивентов listener`а

        Returns:
            asyncio.Queue[Union[PlayerokEvent, AccountEvent]]
        """
        return self._public_queue
    
    
    async def start(
        self,
        *,
        dispatch: bool = True
    ): 
        """
        Запускает listener

        Args:
            dispatch (bool, optional): Если `True` - ивенты автоматически отправляются в зарегестрированные обработчики. Defaults to True.
        """
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        
        elif not self._loop.is_running():
            raise RuntimeError(
                "PlayerokAccountListener.start() требуется запущенный asyncio loop"
            )
        
        self._dispatcher.set_loop(self._loop)
        
        if not self._started:
            self._running = True
            self._websocket.start()
            self._deal_watcher.start()
            self._review_watcher.start()
        
        # _internal_queue -> _public_queue
        self._forward_task = asyncio.create_task(self._forward_loop())
        
        if dispatch and (self._dispatch_task is None or self._dispatch_task.done()):
            if not self._loop or not self._loop.is_running():
                raise RuntimeError(
                    "PlayerokAccountListener.start(dispatch = True) вызов должен осуществляться внутри запущенного цикла asyncio loop"
                )
            
            self._dispatch_task = asyncio.create_task(self._dispatch_loop())
    
    
    async def stop(self):
        """
        Останавливает listener
        """
        await self._websocket.stop()
        await self._deal_watcher.stop()
        await self._review_watcher.stop()
        
        if self._dispatch_task:
            self._dispatch_task.cancel()
        
        if self._forward_task:
            self._forward_task.cancel()
    
    
    async def _dispatch_loop(self):
        """
        Основной цикл отправки ивентов в dispatcher
        
        Берет ивент из публичной очереди и передает их в систему обработчиков
        """
        while True:
            item = await self._public_queue.get()
            
            if isinstance(item, AccountEvent):
                await self._dispatcher.dispatch(item)
            else:
                # PlayerokEvent
                await self._dispatcher.dispatch(
                    AccountEvent(
                        account = self._account,
                        event = item
                    )
                )
    
    
    async def _forward_loop(self):
        """
        Перемещает ивенты из внутренней очереди вотчеров в публичную очередь listener`а
        
        При необходимости оборачивает ивент в `AccountEvent`
        """
        while True:
            event = await self._internal_queue.get()
            
            if self._include_account:
                wrapped = AccountEvent(
                    account = self._account,
                    event = event
                )
                
                await self._public_queue.put(wrapped)
            else:
                await self._public_queue.put(event)
    
    
    
    async def get(self) -> PlayerokEvent | AccountEvent:
        """
        Получает следующий ивент из listener`а

        Returns:
            PlayerokEvent | AccountEvent: Ивент
        """
        return await self._public_queue.get()
    
    
    async def __aiter__(self) -> Self:
        """
        Позволяет использовать listener как асинхронный итератор.
        
        Используется для ручного перебора ивентов в случае `dispatch = False`
        
        Пример использования::

            async for event in listener:
                ...
        """
        return self
    
    async def __anext__(self) -> PlayerokEvent | AccountEvent:
        """
        Возвращает следующее события при async-итерации.
        
        Returns:
            PlayerokEvent | AccountEvent: Ивент
        """
        return await self.get()


class PlayerokMultiAccountListener:
    """
    Класс-обертка над PlayerokAccountListener.
    
    Хранит состяния аккаунтов, всех их listener`ов и принадлежащих к аккаунту ивентов.
    
    Суть работы:
    1. Создает отдельный `PlayerokAccountListener` для каждого аккаунта
    2. Оборачивает `PlayerokEvent` в `AccountEvent` , объединяя все события в единую очередь, состоящую из `AccountEvent`, 
        который содержит в себе аккаунт, которому принадлежит ивент
    3. Передает события в `Dispatcher` 
    
    Поток данных:
    
    `WebsocketClient` -> `DealWatcher` -> `ReviewWatcher` -> `AnyWatcher(custom)` -> `_internal_queue` (`PlayerokEvent`) -> `_forward_loop` ->
        -> `_public_queue` (`AccountEvent`) -> `PlayerokMultiAccountListener.queue` -> `_dispatch_loop` -> `EventDispatcher` -> `Handlers (router)`
    """
    def __init__(
        self,
        accounts: Iterable[AccountClient],
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        queue_maxsize: int = 0,
    ):
        """
        Args:
            accounts (Iterable[AccountClient]): Список аккаунтов
            loop (Optional[asyncio.AbstractEventLoop], optional): Asyncio event loop в котором будет работать listener. Defaults to None.
            queue_maxsize (int, optional): Максимальный размер публичной очереди. Defaults to 0.
        """
        self._loop = loop
        
        # Union[PlayerokEvent, AccountEvent] используется для исправления инвариативности generics в typing
        # На самом деле очередь имеет сигнатуру: asyncio.Queue[AccountEvent]
        self._queue: asyncio.Queue[Union[PlayerokEvent, AccountEvent]] = asyncio.Queue(maxsize = queue_maxsize)
        
        self._dispatcher = EventDispatcher(loop = self._loop)
        self._router = PlayerokRouter(dispatcher = self._dispatcher)
        
        self._dispatch_task: Optional[asyncio.Task] = None
        
        self._listeners = [
            PlayerokAccountListener(
                account = account,
                loop = self._loop,
                queue = self._queue,
                include_account = True
            )
            for account in accounts
        ]
    
    @property
    def listeners(self) -> List[PlayerokAccountListener]:
        """
        Возвращает список всех `PlayerokAccountListener`

        Returns:
            List[PlayerokAccountListener]: список `PlayerokAccountListener`
        """
        return self._listeners
    
    @property
    def queue(self) -> asyncio.Queue[Union[PlayerokEvent, AccountEvent]]:
        """
        Возвращает публичную очередь ивентов listener`а

        Returns:
            asyncio.Queue[Union[PlayerokEvent, AccountEvent]]
        """
        return self._queue
    
    
    async def start(
        self,
        *,
        dispatch: bool = True
    ):
        """
        Запускает все listener`ы

        Args:
            dispatch (bool, optional): Если `True` - ивенты автоматически отправляются в зарегестрированные обработчики. Defaults to True.

        Raises:
            RuntimeError: Если `loop` не запущен
        """
        if self._loop is None:
            self._loop = asyncio.get_running_loop()

        elif not self._loop.is_running():
            raise RuntimeError(
                "MultiAccountListener.start() требуется запущенный asyncio loop"
            )
        
        self._dispatcher.set_loop(self._loop)
        
        for listener in self._listeners:
            listener._loop = self._loop
            await listener.start(dispatch = False)
        
        if dispatch and (self._dispatch_task is None or self._dispatch_task.done()):
            if not self._loop or not self._loop.is_running():
                raise RuntimeError(
                    "MultiAccountListener.start(dispatch = True) вызов должен осуществляться внутри запущенного цикла asyncio loop"
                )
            
            self._dispatch_task = self._loop.create_task(self._dispatch_loop())
    
    
    async def stop(self):
        """
        Останавливает все listener`ы
        """
        for listener in self._listeners:
            await listener.stop()
        
        if self._dispatch_task and not self._dispatch_task.done():
            self._dispatch_task.cancel()
    
    
    async def _dispatch_loop(self):
        """
        Основной цикл обработки ивентов.
        
        Получает ивент из общей очереди и передает в систему обработчиков
        """
        while True:
            item = await self._queue.get()
            
            if isinstance(item, AccountEvent):
                await self._dispatcher.dispatch(item)
    
    
    async def get(self) -> AccountEvent:
        """
        Получает следующий ивент из очереди

        Raises:
            TypeError: Если очередь содержит ивенты, не являющиеся `AccountEvent`

        Returns:
            AccountEvent: Ивент
        """
        item = await self._queue.get()

        if isinstance(item, AccountEvent):
            return item

        raise TypeError(
            "MultiAccountListener очередь имеет ивенты не связанные с аккаунтом"
        )
    
    
    def __aiter__(self) -> Self:
        """
        Позволяет использовать listener как асинхронный итератор.
        
        Используется для ручного перебора ивентов в случае `dispatch = False`
        
        Пример использования::

            async for event in listener:
                ...
        """
        return self

    async def __anext__(self) -> AccountEvent:
        """
        Возвращает следующее события при async-итерации.

        Returns:
            AccountEvent: Ивент
        """
        return await self.get()