# -*- coding: utf-8 -*-

from __future__ import annotations

import asyncio
import time
from typing import Optional, Awaitable

from .base import AccountBase
from ..graphql import (
    build_query_payload,
    build_persisted_query_payload,
)
from .account_proxy import AccountProxy
from ..types.exceptions import UnauthorizedError, MissingAttributeError
from ..models.account import AccountProfile
from ..models.user import UserProfile


class ProfileMixin(AccountBase):
    """
    Миксин профиля аккаунта.
    """
    
    _account_data: Optional[AccountProfile] = None
    _account_last_update: float = 0
    
    ACCOUNT_TTL = 1800 # 30 минут
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._account_lock: asyncio.Lock = asyncio.Lock()
    

    @property
    def me(self) -> Awaitable[AccountProfile]:
        return AccountProxy(self)
    
    
    async def get_me(
        self,
        force_reload: bool = False
    ) -> AccountProfile:
        """
        Возвращает данные о профиле аккаунта
        
        Сохраняет данные в кеше 30 минут, по истечению времени - обновляет данные, если метод был вызван по истечению TTL

        Args:
            force_reload (bool, optional): `True` - если необходимо принудительно обновить данные. Defaults to False.

        Returns:
            AccountProfile: Профиль аккаунта
        """
        async with self._account_lock:
            now = time.time()
            
            if (
                not force_reload
                and self._account_data
                and (now - self._account_last_update) < self.ACCOUNT_TTL
            ):
                return self._account_data
            
            account = await self._fetch_account()
            
            self._account_data = account
            self._account_last_update = now
            
            return account


    async def get_user(
        self, 
        id: str = None, # type: ignore
        username: str = None # type: ignore
    ) -> UserProfile:
        """
        Возвращает профиль пользователя по параметру.
        """
        
        if not any([id, username]):
            raise MissingAttributeError("Не был передан обязательный параметр: id/username")

        payload = build_persisted_query_payload(
            operation_name = "user",
            hash_key = "user",
            variables = {
                "id": id,
                "username": username,
                "hasSupportAccess": False,
            },
        )

        response = await self.transport.request(
            method = "get",
            payload = payload,
        )

        user_data = response.json().get("data", {}).get("user")
        user_data_type = user_data.get("__typename")
        
        if user_data_type == "UserFragment":
            target_user_profile = user_data
        elif user_data_type == "User":
            target_user_profile = user_data.get("profile")
        else:
            target_user_profile = None

        return UserProfile.model_validate(target_user_profile)

    # ================== Helpers ==================
    async def _fetch_account(self) -> AccountProfile:
        payload = build_query_payload(
            operation_name = "viewer",
            query_key = "viewer",
        )
        
        response = await self.transport.request(
            method = "post",
            payload = payload,
        )
        
        # viewer_data = response.json().get("data", {}).get("viewer")
        viewer_data = response.json()["data"]["viewer"]

        if not viewer_data:
            raise UnauthorizedError()

        # Получаем расширенный профиль через persistedQuery
        user_payload = build_persisted_query_payload(
            operation_name = "user",
            hash_key = "user",
            variables = {
                "username": viewer_data.get("username"),
                "hasSupportAccess": False,
            },
        )

        user_response = await self.transport.request(
            method = "get",
            payload = user_payload,
        )
        
        user_data = user_response.json().get("data", {}).get("user")
        
        merged = {**viewer_data, **user_data} # сливаем в единый Dict для валидации
        
        return AccountProfile.model_validate(merged)
    
    
    async def get_account_property(
        self,
        attribute: str
    ):
        account = await self.get_me()
        
        if not hasattr(account, attribute):
            raise AttributeError(f"AccountProfile не имеет атрибута: {attribute}")
        
        return getattr(account, attribute)