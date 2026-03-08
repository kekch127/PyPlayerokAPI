# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Optional

from .profile import ProfileMixin
from ..graphql import build_persisted_query_payload
from ..models.game import (
    GameList,
    Game,
    GameCategory,
    GameCategoryAgreementList,
    GameCategoryDataFieldList,
    GameCategoryInstructionList,
    GameCategoryObtainingTypeList,
)
from ..types.enums import GameTypes, GameCategoryInstructionTypes, GameCategoryDataFieldTypes
from ..types.exceptions import MissingAttributeError

class GameMixin(ProfileMixin):
    """
    Миксин игр
    """
    
    async def get_games(
        self,
        count: int = 24,
        type: Optional[GameTypes] = None,
        after_cursor: str = None, # type: ignore
    ) -> GameList:
        """
        Получает все игры или/и приложения

        Args:
            count (int, optional): Кол-во игр, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            type (Optional[GameTypes], optional): Тип игр, которые нужно получать (Все сразу если не указано). Defaults to None.
            after_cursor (str, optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            GameList: Страница игр
        """
        
        payload = build_persisted_query_payload(
            operation_name = "games",
            hash_key = "games",
            variables = {
                "pagination": {
                    "first": count,
                    "after": after_cursor
                },
                "filter": {
                    "type": type.name if type else None
                }
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("games")

        return GameList.model_validate(result)
    
    
    async def get_game(
        self,
        id: Optional[str] = None,
        slug: Optional[str] = None
    ) -> Game:
        """
        Получает игру/приложение.
        Можно получить по любому из двух параметров:

        Args:
            id (Optional[str], optional): ID игры/приложения. Defaults to None.
            slug (Optional[str], optional): Имя страницы игры/приложения. Defaults to None.

        Returns:
            Game: Модель игры
        """
        
        if not any([id, slug]):
            raise MissingAttributeError("Не был указан обязательный параметр: id/slug")
        
        payload = build_persisted_query_payload(
            operation_name = "GamePage",
            hash_key = "GamePage",
            variables = {
                "id": id,
                "slug": slug
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("game")

        return Game.model_validate(result)
    
    
    
    async def get_game_category(
        self,
        id: Optional[str] = None,
        game_id: Optional[str] = None,
        slug: Optional[str] = None
    ) -> GameCategory:
        """
        Получает категорию игры/приложения.
        Можно получить параметру `id` или по связке параметров `game_id` и `slug`

        Args:
            id (Optional[str], optional): ID категории. Defaults to None.
            game_id (Optional[str], optional): ID игры категории (лучше указывать в связке со slug, чтобы находить точную категорию). Defaults to None.
            slug (Optional[str], optional): Имя страницы категории. Defaults to None.

        Returns:
            GameCategory: Модель категории игры
        """
        
        if not id and not all([game_id, slug]):
            if not id and (game_id or slug):
                raise MissingAttributeError("Связка аргументов game_id, slug была передана не полностью")
            raise MissingAttributeError("Не был передан ни один из обязательных аргументов: id, game_id, slug")
    
        payload = build_persisted_query_payload(
            operation_name = "GamePageCategory",
            hash_key = "GamePageCategory",
            variables = {
                "id": id,
                "gameId": game_id,
                "slug": slug
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("gameCategory")
        
        return GameCategory.model_validate(result)
    
    
    async def get_game_category_agreements(
        self,
        game_category_id: str,
        count: int = 24,
        user_id: Optional[str] = None,
        after_cursor: Optional[str] = None
    ) -> GameCategoryAgreementList:
        """
        Получает соглашения пользователя на продажу предметов в категории (если пользователь уже принял эти соглашения - список будет пуст).

        Args:
            game_category_id (str): ID категории игры
            count (int, optional): Кол-во соглашений, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            user_id (Optional[str], optional): ID пользователя, чьи соглашения нужно получить. Если не указан, будет получать по ID вашего аккаунта. Defaults to None.
            after_cursor (Optional[str], optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            GameCategoryAgreementList: Страница соглашений
        """
        
        payload = build_persisted_query_payload(
            operation_name = "gameCategoryAgreements",
            hash_key = "gameCategoryAgreements",
            variables = {
                "pagination": {
                    "first": count,
                    "after": after_cursor
                },
                "filter": {
                    "gameCategoryId": game_category_id,
                    "userId": user_id or self.get_account_property("id"), # user_id else self.account_data.id
                }
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("gameCategoryAgreements")
        
        return GameCategoryAgreementList.model_validate(result)
    
    
    async def get_game_category_obtaining_types(
        self,
        game_category_id: str,
        count: int = 24,
        after_cursor: Optional[str] = None
    ) -> GameCategoryObtainingTypeList:
        """
        Получает типы (способы) получения предмета в категории.

        Args:
            game_category_id (str): ID категории игры.
            count (int, optional): Кол-во соглашений, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            after_cursor (Optional[str], optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            GameCategoryObtainingTypeList: Страница способов получени
        """
        
        payload = build_persisted_query_payload(
            operation_name = "gameCategoryObtainingTypes",
            hash_key = "gameCategoryObtainingTypes",
            variables = {
                "pagination": {
                    "first": count,
                    "after": after_cursor
                },
                "filter": {
                    "gameCategoryId": game_category_id
                }
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("gameCategoryObtainingTypes")

        return GameCategoryObtainingTypeList.model_validate(result)
    
    
    
    async def get_game_category_instructions(
        self,
        game_category_id: str,
        obtaining_type_id: str,
        count: int = 24,
        type: Optional[GameCategoryInstructionTypes] = None,
        after_cursor: Optional[str] = None
    ) -> GameCategoryInstructionList:
        """
        Получает инструкции по продаже/покупке в категории.

        Args:
            game_category_id (str): ID категории игры
            obtaining_type_id (str): ID типа (способа) получения предмета
            count (int, optional): Кол-во инструкций, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            type (Optional[GameCategoryInstructionTypes], optional): Тип инструкции: для продавца или для покупателя. Defaults to None.
            after_cursor (Optional[str], optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            GameCategoryInstructionList: Информацию о странице инструкии по продаже/покупке в категории
        """
        
        payload = build_persisted_query_payload(
            operation_name = "gameCategoryInstructions",
            hash_key = "gameCategoryInstructions",
            variables = {
                "pagination": {
                    "first": count,
                    "after": after_cursor
                },
                "filter": {
                    "gameCategoryId": game_category_id,
                    "obtainingTypeId": obtaining_type_id,
                    "type": type.name if type else None
                }
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("gameCategoryInstructions")
        
        return GameCategoryInstructionList.model_validate(result)
    
    
    async def get_game_category_data_fields(
        self,
        game_category_id: str,
        obtaining_type_id: str,
        count: int = 24,
        type: Optional[GameCategoryDataFieldTypes] = None,
        after_cursor: Optional[str] = None
    ) -> GameCategoryDataFieldList:
        """
        Получает поля с данными категории (которые отправляются после покупки).

        Args:
            game_category_id (str): ID категории игры
            obtaining_type_id (str): ID типа (способа) получения предмета
            count (int, optional):  Кол-во инструкций, которые нужно получить (не более 24 за один запрос). Defaults to 24.
            type (Optional[GameCategoryDataFieldTypes], optional): Тип полей с данными. Defaults to None.
            after_cursor (Optional[str], optional): Курсор, с которого будет идти парсинг (если нет - ищет с самого начала страницы). Defaults to None.

        Returns:
            GameCategoryDataFieldList: Страница полей данных предмета
        """
        
        payload = build_persisted_query_payload(
            operation_name = "gameCategoryDataFields",
            hash_key = "gameCategoryDataFields",
            variables = {
                "pagination": {
                    "first": count,
                    "after": after_cursor
                },
                "filter": {
                    "gameCategoryId": game_category_id,
                    "obtainingTypeId": obtaining_type_id,
                    "type": type.name if type else None
                }
            }
        )
        
        response = await self.transport.request(
            method = "get",
            payload = payload
        )
        
        result = response.json().get("data", {}).get("gameCategoryDataFields")
        
        return GameCategoryDataFieldList.model_validate(result)