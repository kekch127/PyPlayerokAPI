# -*- coding=utf-8 -*-

from __future__ import annotations

from typing import Dict, Type, List

from .base import BaseMarker
from .default import (
    ItemPaidMarker,
    ItemSentMarker,
    DealConfirmedMarker,
    DealConfirmedAutoMarker,
    DealRolledBackMarker,
    DealHasProblemMarker,
    DealProblemResolvedMarker
)


class MarkerRegistry:
    """
    Регистр маркеров.
    
    Каждый маркер представляет собой класс, наследующий BaseMarker,
    который определяет:

        • строковый идентификатор маркера (marker)
        • тип генерируемого события (event_type)
        • логику построения PlayerokEvent

    Registry позволяет:

        • регистрировать встроенные маркеры SDK
        • подключать сторонние маркеры (плагины)
        • динамически расширять систему событий без изменения EventFactory

    Пример использования::
    
        class CustomMarker(BaseMarker):
            marker = "{{CUSTOM}}"
            event_type = EventTypes.CUSTOM_EVENT

        registry.register(CustomMarker)
    """
    def __init__(self):
        self._markers: Dict[str, BaseMarker] = {}
        self._register_default_markers()
    
    
    def _register_default_markers(self):
        default_markers: List[Type[BaseMarker]] = [
            ItemPaidMarker,
            ItemSentMarker,
            DealConfirmedMarker,
            DealConfirmedAutoMarker,
            DealRolledBackMarker,
            DealHasProblemMarker,
            DealProblemResolvedMarker
        ]
        
        for marker in default_markers:
            self.register(marker)
    
    
    def register(
        self,
        marker_cls: Type[BaseMarker]
    ):
        """
        Регистрирует класс маркера.
        
        Если маркер с таким же ключем уже существует - он будет перезаписан.

        Args:
            marker_cls (Type[BaseMarker]): Класс маркера
        """
        instance = marker_cls()
        self._markers[instance.marker] = instance
    
    
    def get(
        self,
        text: str
    ):
        """
        Получает зарегестрированный маркер по тексту

        Args:
            text (str): текст сообщения
        """
        return self._markers.get(text)

    
    def all(self):
        """
        Возвращает список всех зарегестрированных маркеров
        """
        return list(self._markers.values())