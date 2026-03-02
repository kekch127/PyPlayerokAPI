# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .user import UserProfile
    from .etc import FileObject
    from .game import (
        GameCategoryObtainingType,
        GameCategory,
        GameCategoryDataField,
        GameProfile,
    )
    from .transaction import Transaction
    from .chat import Chat
    from .review import Review

from ..types.enums import (
    ItemStatuses, 
    UserTypes, 
    PriorityTypes,
    ItemLogEvents,
    ItemDealStatuses,
    ItemDealDirections,
)


class Item(BaseModel):
    id: str  # ID предмета 
    slug: Optional[str] = None # Имя страницы предмета 
    name: Optional[str] = None # Название предмета 
    description: Optional[str] = None  # Описание предмета
    status: Optional[ItemStatuses] = None  # Статус предмета 
    obtaining_type: Optional[GameCategoryObtainingType] = None  # Способ получения
    price: Optional[int] = None  # Цена предмета 
    raw_price: Optional[int] = Field(None, alias = "rawPrice") # Цена без учёта скидки 
    priority_position: Optional[int] = Field(None, alias = "priorityPosition")  # Приоритетная позиция 
    attachments: Optional[List[FileObject]] = None  # Файлы-приложения 
    attributes: Optional[Dict] = Field(None, alias = "attributes")  # Аттрибуты предмета 
    category: Optional[GameCategory] = None  # Категория игры 
    comment: Optional[str] = None # Комментарий предмета 
    data_fields: Optional[List[GameCategoryDataField]] = None  # Поля данных 
    fee_multiplier: Optional[float] = Field(None, alias = "feeMultiplier")  # Множитель комиссии 
    game: Optional[GameProfile] = None  # Профиль игры
    seller_type: UserTypes = Field(alias = "sellerType")  # Тип продавца
    user: UserProfile  # Профиль продавца
    
    # ===== ENUM CONVERTER =====
    @field_validator("status", mode = "before")
    @classmethod
    def convert_status(cls, v):
        if isinstance(v, str):
            return ItemStatuses[v]
        return v
    
    @field_validator("seller_type", mode = "before")
    @classmethod
    def convert_seller_type(cls, v):
        if isinstance(v, str):
            return UserTypes[v]
        return v
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_attachments(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        attachments = data.get("attachments")
        if attachments:
            data["attachments"] = attachments
        
        return data

    @model_validator(mode = "before")
    def transform_data_fields(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        data_fields = data.get("dataFields")
        if data_fields:
            data["data_fields"] = data_fields
        
        return data

    class Config:
        populate_by_name = True



class MyItem(BaseModel):
    id: str  # ID предмета
    slug: str  # Имя страницы предмета
    name: str  # Название предмета
    description: str  # Описание предмета
    status: ItemStatuses  # Статус предмета
    obtaining_type: Optional[GameCategoryObtainingType]  # Способ получения
    price: int  # Цена предмета
    prev_price: int  # Предыдущая цена
    raw_price: int  # Цена без учёта скидки
    priority_position: int  # Приоритетная позиция
    attachments: List[FileObject]  # Файлы-приложения
    attributes: dict  # Аттрибуты предмета
    buyer: UserProfile  # Профиль покупателя
    category: GameCategory  # Категория игры
    comment: Optional[str] # Комментарий
    data_fields: Optional[List[GameCategoryDataField]]  # Поля данных
    fee_multiplier: float  # Множитель комиссии
    prev_fee_multiplier: float  # Предыдущий множитель комиссии
    seller_notified_about_fee_change: bool  # Уведомлён ли продавец о смене комиссии
    game: GameProfile  # Профиль игры
    seller_type: UserTypes  # Тип продавца
    user: UserProfile  # Профиль продавца
    priority: PriorityTypes  # Статус приоритета
    priority_price: int  # Цена приоритета
    sequence: Optional[int]  # Позиция в таблице
    status_expiration_date: Optional[str] # Дата истечения статуса
    status_description: Optional[str] # Описание статуса
    status_payment: Optional[Transaction]  # Транзакция статуса
    views_counter: int  # Количество просмотров
    is_editable: bool  # Можно ли редактировать
    approval_date: Optional[str] # Дата публикации
    deleted_at: Optional[str] # Дата удаления
    updated_at: Optional[str] # Дата обновления
    created_at: Optional[str] # Дата создания



class ItemProfile(BaseModel):
    id: str  # ID предмета
    slug: str  # Имя страницы предмета
    priority: PriorityTypes  # Приоритет
    status: ItemStatuses  # Статус
    name: str  # Название
    price: int  # Цена
    raw_price: int  # Цена без скидки
    seller_type: UserTypes  # Тип продавца
    attachment: FileObject  # Файл-приложение
    user: UserProfile  # Профиль продавца
    approval_date: str  # Дата одобрения
    priority_position: int  # Приоритетная позиция
    views_counter: Optional[int]  # Количество просмотров
    fee_multiplier: float  # Множитель комиссии
    created_at: str  # Дата создания


class ItemProfilePageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class ItemProfileList(BaseModel):
    items: Optional[List[ItemProfile]] = None  # Предметы страницы
    page_info: ItemProfilePageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount") 


class ItemPriorityStatusPriceRange(BaseModel):
    min: Optional[int] = None  # Минимальная цена
    max: Optional[int] = None  # Максимальная цена


class ItemPriorityStatus(BaseModel):
    id: str  # ID статуса
    price: int  # Цена статуса
    name: str  # Название статуса
    type: PriorityTypes  # Тип статуса
    period: int  # Длительность (в днях)
    price_range: ItemPriorityStatusPriceRange = Field(alias = "priceRange") # Ценовой диапазон
    
    # ===== ENUM CONVERTER =====
    @field_validator("type", mode = "before")
    @classmethod
    def convert_type(cls, v):
        if isinstance(v, str):
            return PriorityTypes[v]
        return v


    class Config:
        populate_by_name = True


class ItemLog(BaseModel):
    id: str  # ID лога
    event: ItemLogEvents  # Событие
    created_at: Optional[str] = Field(None, alias = "createdAt")  # Дата создания
    user: Optional[UserProfile] = None  # Пользователь
    
    # ===== ENUM CONVERTER =====
    @field_validator("event", mode = "before")
    @classmethod
    def convert_event(cls, v):
        if isinstance(v, str):
            return ItemLogEvents[v]
        return v


    class Config:
        populate_by_name = True


class ItemDeal(BaseModel):
    id: str  # ID сделки
    status: ItemDealStatuses  # Статус сделки
    status_expiration_date: Optional[str] = Field(None, alias = "statusExpirationDate")  # Дата истечения статуса
    status_description: Optional[str] = Field(None, alias = "statusDescription")  # Описание статуса
    direction: ItemDealDirections  # Направление сделки
    obtaining: Optional[str] = None  # Получение
    has_problem: Optional[bool] = Field(None, alias = "hasProblem")  # Есть ли проблема
    report_problem_enabled: Optional[bool] = Field(None, alias = "reportProblemEnabled")  # Доступно ли обжалование
    completed_user: Optional[UserProfile] = Field(None, alias = "completedBy")  # Подтвердивший пользователь
    props: Optional[str] = None  # Реквизиты
    previous_status: Optional[ItemDealStatuses] = Field(None, alias = "prevStatus") # Предыдущий статус
    completed_at: Optional[str] = Field(None, alias = "completedAt")  # Дата подтверждения
    created_at: Optional[str] = Field(None, alias = "createdAt") # Дата создания
    logs: Optional[List[ItemLog]] = None  # Логи сделки 
    transaction: Optional[Transaction] = None  # Транзакция 
    user: Optional[UserProfile] = None  # Пользователь сделки 
    chat: Optional[Chat] = None  # Чат сделки 
    item: Optional[Item] = None  # Предмет 
    review: Optional[Review] = None  # Отзыв
    obtaining_fields: Optional[List[GameCategoryDataField]] = None  # Получаемые поля
    comment_from_buyer: Optional[str] = Field(None, alias = "commentFromBuyer")  # Комментарий покупателя
    
    # ===== ENUM CONVERTER =====
    @field_validator("status", "previous_status", mode = "before")
    @classmethod
    def convert_status(cls, v):
        if isinstance(v, str):
            return ItemDealStatuses[v]
        return v
    
    @field_validator("direction", mode = "before")
    @classmethod
    def convert_direction(cls, v):
        if isinstance(v, str):
            return ItemDealDirections[v]
        return v
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_logs(cls, data: Dict):
        if not isinstance(data, dict):
            return data

        logs = data.get("logs")
        if logs:
            data["logs"] = logs

        return data
    
    @model_validator(mode = "before")
    def transform_review(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        review = data.get("testimonial")
        if review:
            data["review"] = review
        
        return data
    
    @model_validator(mode = "before")
    def transform_obtaining_fields(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        obtaining_fields = data.get("obtainingFields")
        if obtaining_fields:
            data["obtaining_fields"] = obtaining_fields
        
        return data
    
    
    class Config:
        populate_by_name = True


class ItemDealPageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class ItemDealList(BaseModel):
    deals: Optional[List[ItemDeal]] = None  # Сделки страницы
    page_info: ItemDealPageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount")  # Общее количество чатов
