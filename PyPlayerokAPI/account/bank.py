# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import List

from .profile import ProfileMixin
from ..graphql import (
    build_query_payload,
    build_persisted_query_payload
)
from ..models.etc import SBPBankMember
from ..models.user import UserBankCardList
from ..types.enums import SortDirections


class BankMixin(ProfileMixin):
    """
    Миксин действий с картами и банками
    """
    
    async def get_sbp_bank_members(self) -> List[SBPBankMember]:
        """
        Получает всех членов банка СБП

        Returns:
            List (SBPBankMember): Список моделей провайдера транзакции
        """
        
        payload = build_persisted_query_payload(
            operation_name = "SbpBankMembers",
            hash_key = "SbpBankMembers"
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )

        result = response.json().get("data", {}).get("sbpBankMembers")

        return [SBPBankMember.model_validate(m) for m in result]
    
    
    async def get_verified_cards(
        self, 
        count: int = 24, 
        after_cursor: str | None = None,
        direction: SortDirections = SortDirections.ASC
    ) -> UserBankCardList:
        """
        Получает верифицированные карты аккаунта

        Args:
            count (int, optional): Кол-во банковских карт, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            after_cursor (str | None, optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.
            direction (SortDirections, optional): Тип сортировки банковских карт. Defaults to SortDirections.ASC.

        Returns:
            UserBankCardList: Страница банковских карт пользователя
        """
        
        payload = build_persisted_query_payload(
            operation_name = "verifiedCards",
            hash_key = "verifiedCards",
            variables = {
                "pagination": {
                    "first": count, 
                    "after": after_cursor
                }, 
                "sort": {
                    "direction": direction.name
                }, 
                "field": "createdAt"
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )

        result = response.json().get("data", {}).get("verifiedCards")

        return UserBankCardList.model_validate(result)
    
    
    async def delete_card(
        self,
        card_id: str
    ) -> bool:
        """
        Удаляет карту из сохранённых в аккаунте

        Args:
            card_id (str): ID банковской карты

        Returns:
            bool: `True`, если карта удалилась, иначе `False`
        """
        
        payload = build_query_payload(
            operation_name = "deleteCard",
            query_key = "deleteCard",
            variables = {
                "input": {
                    "cardId": card_id
                }
            }
        )
        
        response = await self.transport.request(
            method = "post",
            payload = payload
        )

        result = response.json().get("data", {}).get("deleteCard")

        return result