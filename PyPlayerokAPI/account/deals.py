# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional, List

from .profile import ProfileMixin
from ..graphql import (
    build_query_payload,
    build_persisted_query_payload,
)
from ..models.item import ItemDealList, ItemDeal
from ..types.enums import ItemDealStatuses, ItemDealDirections


class DealsMixin(ProfileMixin):
    """
    Миксин сделок аккаунта.
    """
    
    async def get_deals(
        self,
        count: int = 24,
        statuses: Optional[List[ItemDealStatuses]] = None,
        direction: Optional[ItemDealDirections] = None,
        after_cursor: Optional[str] = None
    ) -> ItemDealList:
        """
        Получает сделки аккаунта

        Args:
            count (int, optional): Кол-во сделок, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            statuses (Optional[List[ItemDealStatuses]], optional): Статусы сделок, которые нужно получать. Defaults to None.
            direction (Optional[ItemDealDirections], optional): Направление сделок. Defaults to None.
            after_cursor (str, optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            ItemDealList: Страница сделок
        """
        payload = build_persisted_query_payload(
            operation_name = "deals",
            hash_key = "deals",
            variables = {
                "pagination": {
                    "first": count, 
                    "after": after_cursor
                },
                "filter": {
                    "userId": await self.get_account_property("id"), # self.account_data.id,
                    "direction": direction.name if direction else None,
                    "status": [status.name for status in statuses] if statuses else None
                },
                "showForbiddenImage": True
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("deals")
        
        return ItemDealList.model_validate(result)
    
    
    async def get_deal(
        self,
        deal_id: str
    ) -> ItemDeal:
        """
        Получает сделку

        Args:
            deal_id (str): ID сделки

        Returns:
            ItemDeal: Модель сделки
        """
        payload = build_persisted_query_payload(
            operation_name = "deal",
            hash_key = "deal",
            variables = {
                "id": deal_id,
                "hasSupportAccess": False,
                "showForbiddenImage": True
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("deal")
        
        return ItemDeal.model_validate(result)
    
    
    async def update_deal(
        self,
        deal_id: str,
        new_status: ItemDealStatuses
    ) -> ItemDeal:
        """
        Обновляет статус сделки
        (используется, чтобы подтвердить, оформить возврат и т.д)

        Args:
            deal_id (str): ID сделки
            new_status (ItemDealStatuses): Новый статус сделки

        Returns:
            ItemDeal: Модель сделки
        """
        payload = build_query_payload(
            operation_name = "updateDeal",
            query_key = "updateDeal",
            variables = {
                "input": {
                    "id": deal_id,
                    "status": new_status.name
                }
            }
        )
        
        response = await self.transport.request(
            method = "post",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("updateDeal")
        
        return ItemDeal.model_validate(result)

