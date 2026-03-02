# -*- coding=utf-8 -*-

from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from logging import getLogger
from typing import Awaitable, Dict, List, Optional, Protocol, TypeAlias, Union

from PyPlayerokAPI.types.enums import EventTypes
from PyPlayerokAPI.account import AccountClient
from .event_wrapper import PlayerokEvent
from .account_event import AccountEvent


class AccountEventHandler(Protocol):
    def __call__(self, account_event: AccountEvent) -> Union[None, Awaitable[None]]:
        ...


class SplitEventHandler(Protocol):
    def __call__(self, account: AccountClient, event: PlayerokEvent) -> Union[None, Awaitable[None]]:
        ...


HandlerType: TypeAlias = Union[AccountEventHandler, SplitEventHandler]


class AsyncEventDispatcher:

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        self._handlers: Dict[EventTypes, List[HandlerType]] = defaultdict(list)
        self._loop = loop
        self._logger = getLogger(__name__)

    def set_loop(self, loop: Optional[asyncio.AbstractEventLoop]):
        self._loop = loop

    def register(self, event_type: EventTypes, handler: HandlerType):
        self._handlers[event_type].append(handler)

    async def dispatch(self, account_event: AccountEvent):
        for handler in self._handlers.get(account_event.event.type, []):
            try:
                result = self._call_handler(handler, account_event)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                self._logger.exception("Event handler error")

    def _call_handler(self, handler: HandlerType, account_event: AccountEvent):
        sig = inspect.signature(handler)
        params = list(sig.parameters.values())
        has_varargs = any(p.kind == p.VAR_POSITIONAL for p in params)
        positional = [
            p for p in params
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]

        if has_varargs or len(positional) >= 2:
            return handler(account_event.account, account_event.event) # type: ignore

        return handler(account_event) # type: ignore
