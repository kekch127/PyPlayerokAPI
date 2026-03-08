# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from typing import List, Optional

from .profile import ProfileMixin
from ..graphql import (
    build_query_payload,
    build_persisted_query_payload
)
from ..models.game import GameCategoryOption, GameCategoryDataField
from ..models.item import Item, ItemProfileList, MyItem, ItemProfile, ItemPriorityStatus
from ..types.enums import TransactionProviderIds, ItemStatuses, TransactionPaymentMethodIds
from ..types.exceptions import MissingAttributeError


class ItemsMixin(ProfileMixin):
    """
    Миксин предметов
    """
    
    async def create_item(
        self,
        game_category_id: str, 
        obtaining_type_id: str, 
        name: str, 
        price: int, 
        description: str, 
        options: List[GameCategoryOption], 
        data_fields: List[GameCategoryDataField],
        attachments: List[str]
    ) -> Item:
        """
        Создаёт предмет (после создания помещается в черновик, а не сразу выставляется на продажу)

        Args:
            game_category_id (str): ID категории игры, в которой необходимо создать предмет
            obtaining_type_id (str): ID типа получения предмета
            name (str): Название предмета
            price (int): Цена предмета
            description (str): Описание предмета
            options (List[GameCategoryOption]): Массив **выбранных** опций (аттрибутов) предмета
            data_fields (List[GameCategoryDataField]): массив полей с данными предмета. \n
                !!! Должны быть заполнены данные с типом поля `ITEM_DATA`, то есть те данные, которые указываются при заполнении информации о товаре.
                Поля с типом `OBTAINING_DATA` **заполнять и передавать не нужно**, так как эти данные будет указывать сам покупатель при оформлении предмета.
            attachments (List[str]): Массив файлов-приложений предмета. Указываются пути к файлам

        Returns:
            Item: Модель созданного предмета
        """
        
        pre_payload = build_query_payload(
            operation_name = "createItem",
            query_key = "createItem",
            variables = {
                "input": {
                    "gameCategoryId": game_category_id,
                    "obtainingTypeId": obtaining_type_id,
                    "name": name,
                    "price": int(price),
                    "description": description,
                    "attributes": {option.field: option.value for option in options},
                    "dataFields": [{"fieldId": field.id, "value": field.value} for field in data_fields]
                },
                "attachments": [None] * len(attachments)
            }
        )
        
        map = {}
        files = {}
        
        for i, att in enumerate(attachments, start=1):
            map[str(i)] = [f"variables.attachments.{i-1}"]
            files[str(i)] = open(att, "rb")
        
        payload = {
            "operations": json.dumps(pre_payload),
            "map": json.dumps(map)
        }
        
        response = await self.transport.request(
            method = "post",
            payload = payload,
            files = files
        )

        result = response.json().get("data", {}).get("createItem")

        return Item.model_validate(result)


    async def update_item(
        self,
        id: str, 
        name: Optional[str] = None, 
        price: Optional[int] = None, 
        description: Optional[str] = None, 
        options: Optional[List[GameCategoryOption]] = None, 
        data_fields: Optional[List[GameCategoryDataField]] = None, 
        remove_attachments: Optional[List[str]] = None, 
        add_attachments: Optional[List[str]] = None
    ) -> Item:
        """
        Обновляет предмет аккаунта.

        Args:
            id (str): ID предмета
            name (Optional[str], optional): Название предмета. Defaults to None.
            price (Optional[int], optional): Цена предмета. Defaults to None.
            description (Optional[str], optional): Описание предмета. Defaults to None.
            options (Optional[List[GameCategoryOption]], optional): Массив **выбранных** опций (аттрибутов) предмета. Defaults to None.
            data_fields (Optional[List[GameCategoryDataField]], optional): Массив полей с данными предмета.
                !!! Должны быть заполнены данные с типом поля `ITEM_DATA`, то есть те данные, которые указываются при заполнении информации о товаре.
                Поля с типом `OBTAINING_DATA` **заполнять и передавать не нужно**, так как эти данные будет указывать сам покупатель при оформлении предмета.. Defaults to None.
            remove_attachments (Optional[List[str]], optional): Массив ID файлов-приложений предмета, которые нужно удалить. Defaults to None.
            add_attachments (Optional[List[str]], optional): Массив файлов-приложений предмета, которые нужно добавить. Указываются пути к файлам. Defaults to None.

        Returns:
            Item: Модель обновлённого предмета
        """
        
        pre_payload = build_query_payload(
            operation_name = "updateItem",
            query_key = "updateItem",
            variables = {
                "input": {
                    "id": id
                },
                "addedAttachments": [None] * len(add_attachments) if add_attachments else None
            }
        )
        
        input_filter = pre_payload["variables"]["input"]
        
        if name:
            input_filter["name"] = name
        
        if price:
            input_filter["price"] = int(price)
        
        if description:
            input_filter["description"] = description
        
        if options:
            input_filter["attributes"] = {option.field: option.value for option in options} if options is not None else None
        
        if data_fields:
            input_filter["dataFields"] = [{"fieldId": field.id, "value": field.value} for field in data_fields] if data_fields is not None else None
        
        if remove_attachments:
            input_filter["removedAttachments"] = remove_attachments
        
        map = {}
        files = {}
        
        if add_attachments:
            for i, att in enumerate(add_attachments, start=1):
                map[str(i)] = [f"variables.addedAttachments.{i-1}"]
                files[str(i)] = open(att, "rb")
        
        payload = {
            "operations": json.dumps(pre_payload),
            "map": json.dumps(map)
        }
        
        response = await self.transport.request(
            method = "post",
            payload = payload
        )

        result = response.json().get("data", {}).get("updateItem")

        return Item.model_validate(result)


    async def remove_item(
        self,
        id: str
    ) -> bool:
        """
        Полностью удаляет предмет вашего аккаунта.

        Args:
            id (str): ID предмета
        """
        
        payload = build_query_payload(
            operation_name = "removeItem",
            query_key =  "removeItem",
            variables = {
                "id": id
            }
        )
        
        # TODO: хоть проверку какую-то сделать, всегда True возвращается
        response = await self.transport.request(
            method = "post",
            payload = payload
        )

        return True
    
    
    async def publish_item(
        self,
        item_id: str, 
        priority_status_id: str, 
        transaction_provider_id: TransactionProviderIds = TransactionProviderIds.LOCAL
    ) -> Item:
        """
        Выставляет предмет на продажу

        Args:
            item_id (str): ID предмета
            priority_status_id (str): ID статуса приоритета предмета, под которым его нужно выставить на продажу
            transaction_provider_id (TransactionProviderIds, optional): ID провайдера транзакции. Defaults to TransactionProviderIds.LOCAL.

        Returns:
            Item: Модель опубликованного предмета
        """
        
        payload = build_query_payload(
            operation_name = "publishItem",
            query_key = "publishItem",
            variables = {
                "input": {
                    "transactionProviderId": transaction_provider_id.name,
                    "priorityStatuses": [priority_status_id],
                    "itemId": item_id
                }
            }
        )

        response = await self.transport.request(
            method = "post",
            payload = payload
        )

        result = response.json().get("data", {}).get("publishItem")

        return Item.model_validate(result)
    
    
    async def get_items(
        self, 
        game_id: Optional[str] = None, 
        category_id: Optional[str] = None, 
        count: int = 24,
        status: ItemStatuses = ItemStatuses.APPROVED, 
        after_cursor: Optional[str] = None
    ) -> ItemProfileList:
        """
        Получает предметы игры/приложения.
        Можно получить по любому из двух параметров: `game_id`, `category_id`.

        Args:
            game_id (Optional[str], optional): ID игры/приложения. Defaults to None.
            category_id (Optional[str], optional): ID категории игры/приложения. Defaults to None.
            count (int, optional): Кол-во предеметов, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            status (ItemStatuses, optional): Тип предметов, которые нужно получать: активные или проданные. Defaults to ItemStatuses.APPROVED.
            after_cursor (Optional[str], optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            ItemProfileList:  Страница профилей предметов
        """
        
        if not any([game_id, category_id]):
            raise MissingAttributeError("Не был указан обязательный параметр: game_id/category_id")
        
        payload = build_persisted_query_payload(
            operation_name = "items",
            hash_key = "items",
            variables = {
                "pagination": {
                    "first": count,
                    "after": after_cursor
                },
                "filter": {
                    "gameId": game_id, 
                    "status": [status.name] if status else None
                } 
                if not category_id else {
                    "gameCategoryId": category_id, 
                    "status": [status.name] if status else None
                }
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )

        result = response.json().get("data", {}).get("items")

        return ItemProfileList.model_validate(result)


    async def get_item(
        self,
        id: Optional[str] = None,
        slug: Optional[str] = None
    ) -> Optional[MyItem | Item | ItemProfile]:
        """
        Получает предмет (товар).
        Можно получить по любому из двух параметров:

        Args:
            id (Optional[str], optional): ID предмета. Defaults to None.
            slug (Optional[str], optional): Имя страницы предмета. Defaults to None.

        Returns:
            MyItem | Item | ItemProfile: Модель предмета
        """
        
        if not any([id, slug]):
            raise MissingAttributeError("Не был указан обязательный параметр: id/slug")
        
        payload = build_persisted_query_payload(
            operation_name = "item",
            hash_key = "item",
            variables = {
                "id": id,
                "slug": slug,
                "hasSupportAccess": False,
                "showForbiddenImage": True
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )

        result = response.json().get("data", {}).get("item")
        result_type = result["__typename"]
        
        if result_type == "MyItem": 
            return MyItem.model_validate(result)
        
        if result_type == "ItemProfile":
            return ItemProfile.model_validate(result)
        
        if result_type in ["Item", "ForeignItem"]:
            return Item.model_validate(result)
        
        return None


    async def get_item_priority_statuses(
        self, 
        item_id: str, 
        item_price: str
    ) -> List[ItemPriorityStatus]:
        """
        Получает статусы приоритетов для предмета

        Args:
            item_id (str): ID предмета
            item_price (str): Цена предмета

        Returns:
            List[ItemPriorityStatus]: Массив статусов приоритета предмета
        """
        
        payload = build_persisted_query_payload(
            operation_name = "itemPriorityStatuses",
            hash_key = "itemPriorityStatuses",
            variables = {
                "itemId": item_id,
                "price": int(item_price)
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )

        result = response.json().get("data", {}).get("itemPriorityStatuses")

        return [ItemPriorityStatus.model_validate(s) for s in result]
    
    
    async def increase_item_priority_status(
        self,
        item_id: str, 
        priority_status_id: str, 
        payment_method_id: Optional[TransactionPaymentMethodIds] = None, 
        transaction_provider_id: TransactionProviderIds = TransactionProviderIds.LOCAL
    ) -> Item:
        """
        Повышает статус приоритета предмета

        Args:
            item_id (str): ID предмета
            priority_status_id (str): ID статуса приоритета, на который нужно изменить
            payment_method_id (Optional[TransactionPaymentMethodIds], optional): Метод оплаты. Defaults to None.
            transaction_provider_id (TransactionProviderIds, optional): ID провайдера транзакции (LOCAL - с баланса кошелька на сайте). Defaults to TransactionProviderIds.LOCAL.

        Returns:
            Item: Модель обновлённого предмета
        """
        
        payload = build_query_payload(
            operation_name = "increaseItemPriorityStatus",
            query_key = "increaseItemPriorityStatus",
            variables = {
                "input": {
                    "itemId": item_id,
                    "priorityStatuses": [priority_status_id],
                    "transactionProviderData": {
                        "paymentMethodId": payment_method_id.name if payment_method_id else None
                    },
                    "transactionProviderId": transaction_provider_id.name
                }
            }
        )
        
        response = await self.transport.request(
            method = "post",
            payload = payload
        )

        result = response.json().get("data", {}).get("increaseItemPriorityStatus")

        return Item.model_validate(result)