# -*- coding=utf-8 -*-

from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from logging import getLogger
from typing import Awaitable, Dict, List, Tuple, Optional, Protocol, TypeAlias, Union, cast

from PyPlayerokAPI.types.enums import EventTypes
from PyPlayerokAPI.account import AccountClient
from .event_wrapper import PlayerokEvent
from .account_event import AccountEvent


class AccountEventHandler(Protocol):
    """
    Типовой "Контракт" для хендлера.
    
    Пояснение: обработчик может принимать AccountEvent и возвращает либо `None`, либо `Awaitable`.
    
    Пример допустимых хендлеров::
    
        def handler(event: AccountEvent): 
            ...
        
        async def handler(event: AccountEvent): 
            await ...
    """
    def __call__(
        self,
        account_event: AccountEvent
    ) -> Union[None, Awaitable[None]]:
        ...


class SplitEventHandler(Protocol):
    """
    Типовой "Контракт" для хендлера.
    
    Пояснение: обработчик так-же может принимать `AccountClient` и `PlayerokEvent` как единый объект. Возвращает либо `None`, либо `Awaitable`.
    
    Пример допустимых хендлеров::
    
        def handler(account: AccountClient, event: PlayerokEvent): 
            ...
        
        async def handler(account: AccountClient, event: PlayerokEvent): 
            await ...
    """
    def __call__(
        self,
        account: AccountClient,
        event: PlayerokEvent
    ) -> Union[None, Awaitable[None]]:
        ...


HandlerType: TypeAlias = Union[AccountEventHandler, SplitEventHandler] # Алиас, ивент может быть либо `AccountEventHandler` либо `SplitEventHandler`


class EventDispatcher:
    """
    Ядро маршрутизации событий.
    
    1. Хранит обработчики по типам событий
    2. Поддерживыает два формата handler`ов
    3. Корректно обрабатывает sync и async функции
    4. Изолирует ошибки handler`ов
    """
    def __init__(
        self,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        self._handlers: Dict[EventTypes, List[Tuple[HandlerType, str]]] = defaultdict(list) # {EventTypes.: [(handler1, "account_event"), (handler2. "split"),]}
        self._loop = loop
        self._logger = getLogger(__name__)
    
    
    def set_loop(
        self,
        loop: Optional[asyncio.AbstractEventLoop]
    ):
        self._loop = loop
    
    
    def register(
        self,
        event_type: EventTypes,
        handler: HandlerType
    ):
        """
        Регистрация обработчика. Вызывает ивенту его зарегестрированный обработчик.
        
        Пример::
        
            dispatcher.register(EventTypes.NEW_MESSAGE, my_handler)
            # теперь при `EventTypes.NEW_MESSAGE` будет вызван `my_handler`

        Args:
            event_type (EventTypes): Тип ивента
            handler (HandlerType): Обработчик
        """
        call_style = self._detect_call_style(handler)
        self._handlers[event_type].append((handler, call_style))

    
    def _detect_call_style(
        self,
        handler: HandlerType
    ) -> str:
        """
        Вычисляет тип выполнения хендлера.

        Args:
            handler (HandlerType): Хендлер

        Returns:
            str: Тип хендлера
        """
        func_signature = inspect.signature(handler) # def f(event): ... | async def f(event): ...
        params = list(func_signature.parameters.values()) 
        has_var_args = any(p.kind == p.VAR_POSITIONAL for p in params) # проверяем, есть ли *args
        positional = [ # берем только позиционные аргументы
            p for p in params
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        
        if has_var_args or len(positional) >= 2:
            return "split"
        
        return "account_event"
    
    
    async def dispatch(
        self,
        account_event: AccountEvent
    ):
        """
        Обрабатывает определенное событие установленным обработчиком (хендлером).
        
        Схема работы:
            dispatch(account_event)
                    ↓
            получить тип события
                    ↓
            найти список handler’ов
                    ↓
            для каждого:
                вызвать
                если async → await
                если ошибка → лог

        Args:
            account_event (AccountEvent): Ивент
        """
        for handler, call_style in self._handlers.get(account_event.event.type, []):
            try:
                if call_style == "split":
                    split_handler = cast(SplitEventHandler, handler) # для type-checker
                    result = split_handler(account_event.account, account_event.event)
                else:
                    account_handler = cast(AccountEventHandler, handler) # для type-checker
                    result = account_handler(account_event)
                
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                self._logger.exception(f"Ошибка обработки хендлера: {e}")