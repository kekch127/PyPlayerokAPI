# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import Optional, Union

from ..types.enums import UserTypes


class AccountProfile(BaseModel):
    model_config = ConfigDict(
        populate_by_name = True
    )
    
    id: str
    username: Optional[str] = None
    email: Optional[str] = None

    role: Optional[UserTypes] = None

    balance: Optional["AccountBalance"] = None
    stats: Optional["AccountStats"] = None

    has_frozen_balance: Optional[bool] = Field(None, alias="hasFrozenBalance")
    has_enabled_notifications: Optional[bool] = Field(None, alias="hasEnabledNotifications")
    unread_chats_counter: Optional[int] = Field(None, alias="unreadChatsCounter")

    is_blocked: Optional[bool] = Field(None, alias="isBlocked")
    is_blocked_for: Optional[str] = Field(None, alias="isBlockedFor")
    is_verified: Optional[bool] = Field(None, alias="isVerified")

    created_at: Optional[str] = Field(None, alias="createdAt")
    support_chat_id: Optional[str] = Field(None, alias="supportChatId")
    system_chat_id: Optional[str] = Field(None, alias="systemChatId")

    # используем validation_alias для вложенных Dict в получаемом Dict (Dict[str, Any, Dict[str, Any], ...])
    avatar_url: Optional[str] = Field(None, validation_alias="profile.avatarURL") 
    is_online: Optional[bool] = Field(None, validation_alias="profile.isOnline")
    rating: Optional[int] = Field(None, validation_alias="profile.rating")
    reviews_count: Optional[int] = Field(None, validation_alias="profile.testimonialCounter")

    # ===== ENUM CONVERTER =====

    @field_validator("role", mode = "before")
    @classmethod
    def convert_role(cls, v):
        if isinstance(v, str):
            return UserTypes[v]
        return v


class AccountBalance(BaseModel):
    id: str # ID
    value: Optional[Union[int, float]] = None # Сумма баланса
    frozen: Optional[Union[int, float]] = None # Сумма замороженного баланса
    available: Optional[Union[int, float]] = None # Сумма доступного баланса
    withdrawable: Optional[Union[int, float]] = None # Сумма доступного для вывода баланса
    pending_income: Optional[Union[int, float]] = Field(None, alias = "pendingIncome") # Сумма ожидаемого дохода


class AccountStats(BaseModel):
    items: AccountItemsStats
    deals: AccountDealsStats


class AccountDealsStats(BaseModel):
    incoming: AccountIncomingDealsStats # Входящие сделки
    outgoing: AccountOutgoingDealsStats # Исходящие сделки


class AccountItemsStats(BaseModel):
    total: int # Кол-во предметов (всего)
    finished: int # Кол-во завершенных предметов


class AccountIncomingDealsStats(BaseModel):
    total: int # Исходящих сделок (всего)
    finished: int # Кол-во завершенных сделок


class AccountOutgoingDealsStats(BaseModel):
    total: int # Исходящих сделок (всего)
    finished: int # Кол-во завершенных сделок