# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel, field_validator, model_validator, Field, ConfigDict
from typing import List, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .etc import FileObject

from ..types.enums import (
    GameTypes, 
    GameCategoryAutoConfirmPeriods, 
    GameCategoryOptionTypes, 
    GameCategoryDataFieldTypes, 
    GameCategoryDataFieldInputTypes, 
    GameCategoryAgreementIconTypes
)


class Game(BaseModel):
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    id: str # ID игры
    slug: str # Имя страницы игры/приложения
    name: str # Название игры/приложения
    type: GameTypes # тип
    logo: Optional[FileObject] = None # Лого игры/приложения
    banner: Optional[FileObject] = None # Баннер игры/приложения
    categories: List[GameCategory] # Список категорий игры/приложения
    created_at: Optional[str] = Field(None, alias = "createdAt") # Дата создания
    
    # ===== ENUM CONVERTER =====
    @field_validator("type", mode = "before")
    @classmethod
    def convert_type(cls, v):
        if isinstance(v, str):
            return GameTypes[v]
        return v


class GameProfile(BaseModel):
    # Профиль игры/приложения
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    id: str  # ID игры/приложения
    slug: str  # Имя страницы игры/приложения
    name: str  # Название игры/приложения
    type: GameTypes  # Тип (игра или приложение)
    logo: Optional[FileObject]  # Лого игры/приложения
    
    # ===== ENUM CONVERTER =====
    @field_validator("type", mode = "before")
    @classmethod
    def convert_type(cls, v):
        if isinstance(v, str):
            return GameTypes[v]
        return v


class GamePageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class GameList(BaseModel):
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    games: Optional[List[GameProfile]] = None  # Игры/приложения страницы
    page_info: GamePageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount")
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_games(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        edges = data.get("edges")
        if edges:
            data["games"] = [game.get("node") for game in edges]
        
        return data


class GameCategory(BaseModel):
    # Категория игры/приложения
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    id: str  # ID категории
    slug: Optional[str] = None  # Имя страницы категории
    name: Optional[str] = None  # Название категории
    category_id: Optional[str] = Field(None, alias = "categoryId")  # ID родительской категории
    game_id: Optional[str] = Field(None, alias = "gameId") # ID игры категории
    obtaining: Optional[str] = None  # Тип получения
    options: Optional[List[GameCategoryOption]] = None # Опции категории
    props: Optional[GameCategoryProps] = None  # Пропорции категории 
    no_comment_from_buyer: Optional[bool] = Field(None, alias = "noCommentFromBuyer")  # Без комментария от покупателя
    instruction_for_buyer: Optional[str] = Field(None, alias = "instructionForBuyer") # Инструкция для покупателя
    instruction_for_seller: Optional[str] = Field(None, alias = "instructionForSeller") # Инструкция для продавца
    use_custom_obtaining: Optional[bool] = Field(None, alias = "useCustomObtaining") # Используется ли кастомное получение
    auto_confirm_period: Optional[GameCategoryAutoConfirmPeriods] = None # Период авто-подтверждения 
    auto_moderation_mode: Optional[bool] = Field(None, alias = "autoModerationMode")  # Включена ли авто-модерация
    agreements: Optional[List[GameCategoryAgreement]] = None  # Соглашения покупателя 
    fee_multiplier: Optional[float] = Field(None, alias = "feeMultiplier")  # Множитель комиссии
    
    # ===== ENUM CONVERTER =====
    @field_validator("auto_confirm_period", mode = "before")
    @classmethod
    def convert_auto_confirm_period(cls, v):
        if isinstance(v, str):
            return GameCategoryAutoConfirmPeriods[v]
        return v
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_categories(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        categories = data.get("categories")
        if categories:
            data["categories"] = categories
        
        return data

    @model_validator(mode = "before")
    def transform_options(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        options = data.get("options")
        if options:
            data["options"] = options
        
        return data
    
    @model_validator(mode = "before")
    def transform_agreements(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        agreements = data.get("agreements")
        if agreements:
            data["agreements"] = agreements
        
        return data
    
    @model_validator(mode = "before")
    def transform_props(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        props = data.get("props")
        if props:
            data["props"] = props
        
        return data


class GameCategoryProps(BaseModel):
    # Ограничения категории
    
    min_reviews: Optional[int] = Field(None, alias = "minTestimonials")  # Минимальное количество отзывов
    min_reviews_for_seller: Optional[int] = Field(None, alias = "minTestimonialsForSeller")  # Минимальное количество отзывов для продавца


class GameCategoryOption(BaseModel):
    # Опция категории
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    id: str  # ID опции
    group: Optional[str]  # Группа опции
    label: Optional[str]  # Название опции
    type: GameCategoryOptionTypes  # Тип опции
    field: str  # Название поля для payload
    value: Optional[str]  # Значение поля
    value_range_limit: Optional[int] = Field(None, alias = "valueRangeLimit")  # Лимит разброса значения
    
    # ===== ENUM CONVERTER =====
    @field_validator("type", mode = "before")
    @classmethod
    def convert_type(cls, v):
        if isinstance(v, str):
            return GameCategoryOptionTypes[v]
        return v


class GameCategoryInstruction(BaseModel):
    # Информацию о странице инструкии по продаже/покупке в категории.
    
    id: str  # ID инструкции
    text: str  # Текст инструкции


class GameCategoryInstructionPageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class GameCategoryInstructionList(BaseModel):
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    instructions: Optional[List[GameCategoryInstruction]] = None  # Инструкции страницы
    page_info: GameCategoryInstructionPageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount")
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_instructions(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        edges = data.get("edges")
        if edges:
            data["instructions"] = [instruction.get("node") for instruction in edges]
        
        return data


class GameCategoryAgreement(BaseModel):
    # Соглашение покупателя
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    id: str  # ID соглашения
    description: Optional[str]  # Описание соглашения
    icontype: Optional[GameCategoryAgreementIconTypes] = Field(None, alias = "iconType")  # Тип иконки
    sequence: Optional[int]  # Порядок отображения
    
    # ===== ENUM CONVERTER =====
    @field_validator("icontype", mode = "before")
    @classmethod
    def convert_icontype(cls, v):
        if isinstance(v, str):
            return GameCategoryAgreementIconTypes[v]
        return v


class GameCategoryAgreementPageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class GameCategoryAgreementList(BaseModel):
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    agreements: Optional[List[GameCategoryAgreement]] = None  # Соглашения страницы
    page_info: GameCategoryAgreementPageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount")
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_agreements(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        edges = data.get("edges")
        if edges:
            data["agreements"] = [agreement.get("node") for agreement in edges]
        
        return data


class GameCategoryObtainingType(BaseModel):
    # Способ получени предмета
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    id: str  # ID способа
    name: str  # Название способа
    description: Optional[str] = None # Описание способа
    game_category_id: Optional[str] = Field(None, alias = "gameCategoryId")  # ID категории
    no_comment_from_buyer: Optional[bool] = Field(None, alias = "noCommentFromBuyer")  # Без комментария от покупателя
    instruction_for_buyer: Optional[str] = Field(None, alias = "instructionForBuyer")  # Инструкция для покупателя
    instruction_for_seller: Optional[str] = Field(None, alias = "instructionForSeller") # Инструкция для продавца
    sequence: int  # Порядок отображения
    fee_multiplier: Optional[float] = Field(None, alias = "feeMultiplier")  # Множитель комиссии
    agreements: List[GameCategoryAgreement]  # Соглашения 
    props: Optional[GameCategoryProps] = None  # Ограничения категории 
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_agreements(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        agreements = data.get("agreements")
        if agreements:
            data["agreements"] = agreements
        
        return data

    @model_validator(mode = "before")
    def transform_props(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        props = data.get("props")
        if props:
            data["props"] = props
        
        return data


class GameCategoryObtainingTypePageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class GameCategoryObtainingTypeList(BaseModel):
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    obtaining_types: Optional[List[GameCategoryObtainingType]] = None  # Способы получения
    page_info: GameCategoryObtainingTypePageInfo= Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount")
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_obtaining_types(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        edges = data.get("edges")
        if edges:
            data["obtaining_types"] = [type.get("node") for type in edges]
        
        return data


class GameCategoryDataField(BaseModel):
    # Поля данных предмета
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    id: str  # ID поля
    label: Optional[str] = None  # Название поля
    type: Optional[GameCategoryDataFieldTypes] = None  # Тип поля
    input_type: Optional[GameCategoryDataFieldInputTypes] = None # Тип ввода
    copyable: Optional[bool] = None  # Разрешено копирование
    hidden: Optional[bool] = None  # Скрыто ли поле
    required: Optional[bool] = None  # Обязательное ли поле
    value: Optional[str]  = None # Значение поля
    
    # ===== ENUM CONVERTER =====
    @field_validator("type", mode = "before")
    @classmethod
    def convert_type(cls, v):
        if isinstance(v, str):
            return GameCategoryDataFieldTypes[v]
        return v

    @field_validator("input_type", mode = "before")
    @classmethod
    def convert_input_type(cls, v):
        if isinstance(v, str):
            return GameCategoryDataFieldInputTypes[v]
        return v


class GameCategoryDataFieldPageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class GameCategoryDataFieldList(BaseModel):
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    data_fields: Optional[List[GameCategoryDataField]] = None  # Поля данных страницы
    page_info: GameCategoryDataFieldPageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount")
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_data_fields(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        edges = data.get("edges")
        if edges:
            data["data_fields"] = [data_field.get("node") for data_field in edges]
        
        return data