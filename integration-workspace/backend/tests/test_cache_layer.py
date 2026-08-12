from app.core.cache import get_cache_health, get_transient_cache, reset_transient_cache


def test_transient_cache_memory_fallback_round_trip() -> None:
    reset_transient_cache()
    cache = get_transient_cache()

    cache.set_json("session:test", {"value": 42}, ttl_seconds=60)

    assert cache.ping() is True
    assert cache.get_json("session:test") == {"value": 42}
    cache.delete("session:test")
    assert cache.get_json("session:test") is None


def test_cache_health_reports_mode() -> None:
    reset_transient_cache()

    health = get_cache_health()

    assert health.ready is True
    assert health.mode in {"memory", "redis"} or health.mode.startswith("provexa")
