# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel, model_validator, field_validator, Field
from typing import List, Optional, TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from .item import ItemDeal
    from .user import UserProfile
    from .etc import Moderator

from ..types.enums import ReviewStatuses

class Review(BaseModel):
    # Объект отзыва

    id: str  # ID отзыва
    status: Optional[ReviewStatuses] = None  # Статус отзыва
    text: Optional[str] = None # Текст отзыва
    rating: Optional[int] = None  # Рейтинг отзыва
    created_at: Optional[str] = Field(None, alias = "createdAt")  # Дата создания
    updated_at: Optional[str] = Field(None, alias = "updatedAt")  # Дата изменения
    deal: Optional[ItemDeal] = None  # Сделка, связанная с отзывом
    creator: Optional[UserProfile] = None  # Создатель отзыва 
    moderator: Optional[Moderator] = None  # Модератор, обработавший отзыв 
    user: Optional[UserProfile] = None  # Продавец, к которому относится отзыв
    
    
    # ===== ENUM CONVERTER =====
    @field_validator("status", mode = "before")
    @classmethod
    def convert_status(cls, v):
        if isinstance(v, str):
            return ReviewStatuses[v]
        return v


    class Config:
        populate_by_name = True


class ReviewPageInfo(BaseModel):
    start_cursor: Optional[str] = Field(None, alias = "startCursor")  # Курсор начала страницы
    end_cursor: Optional[str] = Field(None, alias = "endCursor")  # Курсор конца страницы
    has_previous_page: Optional[bool] = Field(None, alias = "hasPreviousPage")  # Есть предыдущая страница
    has_next_page: Optional[bool] = Field(None, alias = "hasNextPage")  # Есть следующая страница


class ReviewList(BaseModel):
    reviews: Optional[List[Review]] = None # Отзывы страницы
    page_info: ReviewPageInfo = Field(alias = "pageInfo")  # Информация о странице
    total_count: int = Field(alias = "totalCount") 
