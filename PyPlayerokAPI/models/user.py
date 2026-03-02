# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict

from ..types.enums import UserTypes, BankCardTypes


class UserProfile(BaseModel):
    id: str # ID 
    username: str = Field("Поддержка") # Никнейм 
    role: Optional[UserTypes] = None # Роль
    avatar_url: Optional[str] = Field(None, alias = "avatarURL") # Ссылка на аватар
    is_online: Optional[bool] = Field(None, alias = "isOnline") # Статус онлайна в данный момент
    is_blocked: Optional[bool] = Field(None, alias = "isBlocked") # Статус блокировки
    rating: Optional[int] = None # Рейтинг (0-5)
    reviews_count: Optional[int] = Field(None, alias = "testimonialCounter") # Кол-во отзывов
    support_chat_id: Optional[str] = Field(None, alias = "supportChatId") # ID чата поддержки
    system_chat_id: Optional[str] = Field(None, alias = "systemChatId")  # ID системного чата
    created_at: Optional[str] = Field(None, alias = "createdAt") # Дата создания
    
    # self.__account: Account | None = get_account() Объект аккаунта (для методов)
    
    # ===== ENUM CONVERTER =====
    @field_validator("role", mode = "before")
    @classmethod
    def convert_role(cls, v):
        if isinstance(v, str):
            return UserTypes[v]
        return v


class UserBankCard(BaseModel):
    id: str # ID карты
    card_first_six: Optional[str] = Field(None, alias = "cardFirstSix") # Первые 6 цифр карты 
    card_last_four: Optional[str] = Field(None, alias = "cardLastFour") # Последние 4 цифры карты
    card_type: Optional[BankCardTypes] = Field(None, alias = "cardType") # Тип карты
    is_chosen: Optional[bool] = Field(None, alias = "isChosen") # Выбрана ли по умолчанию?
    
    # ===== ENUM CONVERTER =====
    @field_validator("card_type", mode = "before")
    @classmethod
    def convert_card_type(cls, v):
        if isinstance(v, str):
            return BankCardTypes[v]
        return v


    class Config:
        populate_by_name = True


class UserBankCardList(BaseModel):
    bank_cards: Optional[List[UserBankCard]] = None
    page_info: UserBankCastPageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount") 
    
    # ===== MODEL CONVERTER =====
    @model_validator(mode = "before")
    def transform_bank_cards(cls, data: Dict):
        if not isinstance(data, dict):
            return data
        
        bank_cards = data.get("node")
        if bank_cards:
            data["bank_cards"] = bank_cards
        
        return data


    class Config:
        populate_by_name = True


class UserBankCastPageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница