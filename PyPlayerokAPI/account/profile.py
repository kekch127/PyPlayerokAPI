# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from .base import AccountBase
from ..graphql import (
    build_query_payload,
    build_persisted_query_payload,
)
from ..types.exceptions import UnauthorizedError, MissingAttributeError
from ..models.account import AccountProfile
from ..models.user import UserProfile


class ProfileMixin(AccountBase):
    """
    Миксин профиля аккаунта.
    """
    
    _account_data: Optional[AccountProfile] = None


    @property
    def account_data(self):
        """
        Возвращает кэшированный профиль аккаунта.
        При первом вызове -> загружает его
        """
        return self.get()


    def get(
        self,
        force_reload: bool = False    
    ) -> AccountProfile:
        """
        Возвращает профиль текущего аккаунта (viewer).

        Args:
            force_reload (bool, optional): Принудительное обновление информации аккаунта. Defaults to False.
        """
        
        if self._account_data and not force_reload:
            return self._account_data


        payload = build_query_payload(
            operation_name = "viewer",
            query_key = "viewer",
        )

        response = self.transport.request(
            method = "post",
            payload = payload,
        )

        viewer_data = response.json().get("data", {}).get("viewer")

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

        user_response = self.transport.request(
            method = "get",
            payload = user_payload,
        )

        user_data = user_response.json().get("data", {}).get("user")
        
        merged = {**viewer_data, **user_data} # сливаем в единый Dict для валидации

        account = AccountProfile.model_validate(merged)
        
        self._account_data = account
        return account



    def get_user(
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

        response = self.transport.request(
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