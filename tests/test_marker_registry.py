from PyPlayerokAPI.stream.events.markers.registry import MarkerRegistry


def test_registry_has_markers():
    registry = MarkerRegistry()

    marker = registry.get("{{ITEM_PAID}}")

    assert marker is not None


def test_unknown_marker():
    registry = MarkerRegistry()

    marker = registry.get("UNKNOWN_MARKER")

    assert marker is None