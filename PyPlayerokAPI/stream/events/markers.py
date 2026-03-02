# -*- coding=utf-8 -*-

from PyPlayerokAPI.types.enums import EventTypes
from PyPlayerokAPI.models.chat import Chat, ChatMessage
from .event_wrapper import PlayerokEvent
from .event_factory import EventFactory


def register_default_markers(factory: EventFactory):

    def item_paid(factory: EventFactory, message: ChatMessage, chat: Chat):
        deal = message.deal
        if not deal:
            return []

        factory.mark_review_check(deal.id)

        if not factory.mark_processed(deal.id):
            return []

        return [
            PlayerokEvent(type=EventTypes.NEW_DEAL, chat=chat, deal=deal, message=message),
            PlayerokEvent(type=EventTypes.ITEM_PAID, chat=chat, deal=deal, message=message),
        ]

    def item_sent(factory: EventFactory, message: ChatMessage, chat: Chat):
        deal = message.deal
        if not deal:
            return []

        return [
            PlayerokEvent(type=EventTypes.ITEM_SENT, chat=chat, deal=deal, message=message),
            PlayerokEvent(type=EventTypes.DEAL_STATUS_CHANGED, chat=chat, deal=deal, message=message),
        ]

    def confirmed(factory: EventFactory, message: ChatMessage, chat: Chat):
        deal = message.deal
        if not deal:
            return []

        return [
            PlayerokEvent(type=EventTypes.DEAL_CONFIRMED, chat=chat, deal=deal, message=message),
            PlayerokEvent(type=EventTypes.DEAL_STATUS_CHANGED, chat=chat, deal=deal, message=message),
        ]

    def confirmed_auto(factory: EventFactory, message: ChatMessage, chat: Chat):
        deal = message.deal
        if not deal:
            return []

        return [
            PlayerokEvent(type=EventTypes.DEAL_CONFIRMED_AUTOMATICALLY, chat=chat, deal=deal, message=message),
            PlayerokEvent(type=EventTypes.DEAL_STATUS_CHANGED, chat=chat, deal=deal, message=message),
        ]

    def rolled_back(factory: EventFactory, message: ChatMessage, chat: Chat):
        deal = message.deal
        if not deal:
            return []

        return [
            PlayerokEvent(type=EventTypes.DEAL_ROLLED_BACK, chat=chat, deal=deal, message=message),
            PlayerokEvent(type=EventTypes.DEAL_STATUS_CHANGED, chat=chat, deal=deal, message=message),
        ]

    def has_problem(factory: EventFactory, message: ChatMessage, chat: Chat):
        deal = message.deal
        if not deal:
            return []

        return [
            PlayerokEvent(type=EventTypes.DEAL_HAS_PROBLEM, chat=chat, deal=deal, message=message),
            PlayerokEvent(type=EventTypes.DEAL_STATUS_CHANGED, chat=chat, deal=deal, message=message),
        ]

    def problem_resolved(factory: EventFactory, message: ChatMessage, chat: Chat):
        deal = message.deal
        if not deal:
            return []

        return [
            PlayerokEvent(type=EventTypes.DEAL_PROBLEM_RESOLVED, chat=chat, deal=deal, message=message),
            PlayerokEvent(type=EventTypes.DEAL_STATUS_CHANGED, chat=chat, deal=deal, message=message),
        ]

    factory.register_marker("{{ITEM_PAID}}", item_paid)
    factory.register_marker("{{ITEM_SENT}}", item_sent)
    factory.register_marker("{{DEAL_CONFIRMED}}", confirmed)
    factory.register_marker("{{DEAL_CONFIRMED_AUTOMATICALLY}}", confirmed_auto)
    factory.register_marker("{{DEAL_ROLLED_BACK}}", rolled_back)
    factory.register_marker("{{DEAL_HAS_PROBLEM}}", has_problem)
    factory.register_marker("{{DEAL_PROBLEM_RESOLVED}}", problem_resolved)
