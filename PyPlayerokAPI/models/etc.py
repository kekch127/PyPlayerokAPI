# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class FileObject(BaseModel):
    id: str
    url: Optional[str] = None
    filename: Optional[str] = None
    mime: Optional[str] = None


class Moderator(BaseModel):
    # TODO: Сделать класс модератора Moderator
    pass


class Event(BaseModel):
    # TODO: Сделать класс ивента Event
    pass


class SBPBankMember(BaseModel):
    # Объект членов СБП банка.

    id: Optional[str] = None # ID
    name: Optional[str] = None # Название
    icon: Optional[str] = None # Ссылка иконки