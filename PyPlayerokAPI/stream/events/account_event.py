# -*- coding=utf-8 -*-

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from PyPlayerokAPI.account import AccountClient
from .event_wrapper import PlayerokEvent


class AccountEvent(BaseModel):
    """
    Класс-обертка события с привязкой к конкретному аккаунту.
    Нужен для связывания события стрима с конкретным аккаунтом, чтобы корректно обрабатывать и маршрутизировать в диспатчере.
    """
    model_config = ConfigDict(
        frozen = True,
        arbitrary_types_allowed = True,
    )
    
    account: AccountClient
    event: PlayerokEvent