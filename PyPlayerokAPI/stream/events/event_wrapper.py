# -*- coding=utf-8 -*-

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict

from PyPlayerokAPI.types.enums import EventTypes
from PyPlayerokAPI.models.chat import Chat, ChatMessage
from PyPlayerokAPI.models.item import ItemDeal


class PlayerokEvent(BaseModel):
    """
    Универсальный класс-обертка ивентов на Playerok
    """
    model_config = ConfigDict(frozen = True)
    
    type: EventTypes
    chat: Optional[Chat] = None
    message: Optional[ChatMessage] = None
    deal: Optional[ItemDeal] = None
