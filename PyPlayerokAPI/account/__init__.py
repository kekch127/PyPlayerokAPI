# -*- coding=utf-8 -*-

from .bank import BankMixin
from .chat import ChatMixin
from .deals import DealsMixin
from .games import GameMixin
from .items import ItemsMixin
from .profile import ProfileMixin
from .transactions import TransactionsMixin


class AccountClient(
    BankMixin,
    ChatMixin,
    DealsMixin,
    GameMixin,
    ItemsMixin,
    TransactionsMixin,
    ProfileMixin,
):
    pass


# Обратная совместимость
Client = AccountClient

__all__ = [
    "AccountClient",
    "Client",
]
