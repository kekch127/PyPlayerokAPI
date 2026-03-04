# -*- coding=utf-8 -*-

from PyPlayerokAPI.types.enums import EventTypes
from .base import BaseMarker


class ItemPaidMarker(BaseMarker):
    marker = "{{ITEM_PAID}}"
    event_type = EventTypes.ITEM_PAID
    include_status_change = False
    deduplicate = True
    review_check = True


class ItemSentMarker(BaseMarker):
    marker = "{{ITEM_SENT}}"
    event_type = EventTypes.ITEM_SENT


class DealConfirmedMarker(BaseMarker):
    marker = "{{DEAL_CONFIRMED}}"
    event_type = EventTypes.DEAL_CONFIRMED


class DealConfirmedAutoMarker(BaseMarker):
    marker = "{{DEAL_CONFIRMED_AUTOMATICALLY}}"
    event_type = EventTypes.DEAL_CONFIRMED_AUTOMATICALLY


class DealRolledBackMarker(BaseMarker):
    marker = "{{DEAL_ROLLED_BACK}}"
    event_type = EventTypes.DEAL_ROLLED_BACK


class DealHasProblemMarker(BaseMarker):
    marker = "{{DEAL_HAS_PROBLEM}}"
    event_type = EventTypes.DEAL_HAS_PROBLEM


class DealProblemResolvedMarker(BaseMarker):
    marker = "{{DEAL_PROBLEM_RESOLVED}}"
    event_type = EventTypes.DEAL_PROBLEM_RESOLVED