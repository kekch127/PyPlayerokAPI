# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel, model_validator, field_validator, Field, ConfigDict
from typing import List, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .game import Game
    from .etc import FileObject, Moderator, Event
    from .user import UserProfile
    from .item import ItemDeal, Item
    from .transaction import Transaction

from ..types.enums import ChatMessageButtonTypes, ChatTypes, ChatStatuses


class ChatMessageButton(BaseModel):
    # Объект кнопки сообщения
    model_config = ConfigDict(
        populate_by_name = True
    )

    type: ChatMessageButtonTypes  # Тип кнопки
    url: Optional[str] = None # URL кнопки
    text: Optional[str] = None  # Текст кнопки
    
    # ===== ENUM CONVERTER =====
    @field_validator("type", mode = "before")
    @classmethod
    def convert_type(cls, v):
        if isinstance(v, str):
            return ChatMessageButtonTypes[v]
        return v


class ChatMessage(BaseModel):
    # Сообщение в чате
    model_config = ConfigDict(
        populate_by_name = True
    )

    id: str  # ID сообщения 
    text: Optional[str] = None # Текст сообщения 
    created_at: Optional[str] = Field(None, alias = "createdAt")  # Дата создания 
    deleted_at: Optional[str] = Field(None, alias = "deletedAt")  # Дата удаления 
    is_read: Optional[bool] = Field(None, alias = "isRead")   # Прочитано ли сообщение 
    is_suspicious: Optional[bool] = Field(None, alias = "isSuspicious")  # Подозрительное ли сообщение 
    is_bulk_messaging: Optional[bool] = Field(None, alias = "isBulkMessaging")   # Массовая рассылка 
    game: Optional[Game] = None # Игра, к которой относится сообщение
    file: Optional[FileObject] = None # Прикреплённый файл 
    user: Optional[UserProfile] = None # Отправитель сообщения 
    deal: Optional[ItemDeal] = None # Сделка сообщения 
    item: Optional[Item] = None # Предмет сообщения 
    transaction: Optional[Transaction] = None  # Транзакция сообщения 
    moderator: Optional[Moderator] = None  # Модератор сообщения 
    event_by_user: Optional[UserProfile] = Field(None, alias = "eventByUser")  # Ивент от пользователя 
    event_to_user: Optional[UserProfile] = Field(None, alias = "eventToUser")  # Ивент для пользователя 
    is_auto_response: Optional[bool] = Field(None, alias = "isAutoResponse")  # Авто-ответ 
    event: Optional[Event] = None  # Ивент сообщения 
    buttons: Optional[List[ChatMessageButton]] = None  # Кнопки сообщения 
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    @classmethod
    def transform_btn(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        buttons = data.get("buttons")
        if buttons:
            data["buttons"] = buttons
        
        return data


class ChatMessagePageInfo(BaseModel):
    # Информация о странице сообщений

    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница
    
    


class ChatMessageList(BaseModel):
    # Страница сообщений чата
    model_config = ConfigDict(
        populate_by_name = True
    )

    messages: Optional[List[ChatMessage]] = None  # Сообщения страницы
    page_info: Optional[ChatMessagePageInfo] = Field(None, alias = "pageInfo")  # Информация о странице
    total_count: Optional[int] = Field(None, alias = "totalCount")  # Общее количество сообщений
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    @classmethod
    def transform_edges(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        edges = data.get("edges")
        if edges:
            data["messages"] = [edge.get("node") for edge in edges]
        
        return data


class Chat(BaseModel):
    # Объект чата
    model_config = ConfigDict(
        populate_by_name = True
    )

    id: str  # ID чата
    type: Optional[ChatTypes] = None  # Тип чата
    status: Optional[ChatStatuses] = None # Статус чата
    unread_messages_counter: Optional[int] = Field(None, alias = "unreadMessagesCounter")  # Количество непрочитанных сообщений
    bookmarked: Optional[bool] = None # В закладках ли чат
    is_texting_allowed: Optional[bool] = Field(None, alias = "isTextingAllowed") # Разрешено ли писать
    owner: Optional[UserProfile] = None  # Владелец чата 
    deals: Optional[List[ItemDeal]] = None # Сделки чата 
    last_message: Optional[ChatMessage] = Field(None, alias = "lastMessage")  # Последнее сообщение 
    users: Optional[List[UserProfile]] = None  # Участники чата  
    started_at: Optional[str] = Field(None, alias = "startedAt") # Дата начала диалога 
    finished_at: Optional[str] = Field(None, alias = "finishedAt") # Дата завершения диалога 
    
    # ===== ENUM CONVERTER =====
    @field_validator("type", mode = "before")
    @classmethod
    def convert_type(cls, v):
        if isinstance(v, str):
            return ChatTypes[v]
        return v
    
    @field_validator("status", mode = "before")
    @classmethod
    def convert_status(cls, v):
        if isinstance(v, str):
            return ChatStatuses[v]
        return v
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    @classmethod
    def transform_participiants(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        participants = data.get("participants")
        if participants:
            data["users"] = participants
        
        return data
    
    @model_validator(mode = "before")
    @classmethod
    def transform_deals(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        deals = data.get("deals")
        if deals:
            data["deals"] = deals
        
        return data


class ChatPageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class ChatList(BaseModel):
    # Страница чатов
    model_config = ConfigDict(
        populate_by_name = True
    )

    chats: List[Chat]  # Чаты страницы
    page_info: ChatPageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount")  # Общее количество чатов

    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    @classmethod
    def transform_edges(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        edges = data.get("edges")
        if edges:
            data["chats"] = [edge.get("node") for edge in edges]
        
        return data