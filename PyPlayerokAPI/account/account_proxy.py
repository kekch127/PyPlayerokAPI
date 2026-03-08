# -*- coding=utf-8 -*-

from typing import Awaitable, Generic, TypeVar
from ..models.account import AccountProfile

T = TypeVar("T")


class AccountAttrProxy(Awaitable[T], Generic[T]):
    def __init__(self, client, attr: str):
        self._client = client
        self._attr = attr

    def __await__(self):
        async def getter():
            profile = await self._client.get_me()
            return getattr(profile, self._attr)
        
        return getter().__await__()


class AccountProxy(Awaitable[AccountProfile]):
    def __init__(self, client):
        self._client = client

    def __await__(self):
        return self._client.get_me().__await__()

    def __getattr__(self, item):
        return AccountAttrProxy(self._client, item)