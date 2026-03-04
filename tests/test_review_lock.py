from PyPlayerokAPI.stream.events.event_factory import EventFactory


def test_review_lock():

    factory = EventFactory()

    factory.mark_review_check("deal1")
    factory.mark_review_check("deal2")

    deals = factory.get_review_check_deals()

    assert "deal1" in deals
    assert "deal2" in deals

    factory.unmark_review_check("deal1")

    deals = factory.get_review_check_deals()

    assert "deal1" not in deals