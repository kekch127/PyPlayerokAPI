# -*- coding=utf-8 -*-

from .account import *
from .chat import *
from .etc import *
from .game import *
from .item import *
from .review import *
from .transaction import *
from .user import *


for model in BaseModel.__subclasses__():
    try:
        model.model_rebuild()
    except Exception as e:
        print(f"FAILED rebuild model: {e}")