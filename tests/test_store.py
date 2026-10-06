import time

from core.store import Store


def test_set_and_get():
    store = Store(max_memory=3)

    store.set("name", "Vinay")

    assert store.get("name") == "Vinay"


def test_get_missing_key():
    store = Store(max_memory=3)

    assert store.get("missing") is None


def test_delete():
    store = Store(max_memory=3)

    store.set("name", "Vinay")

    assert store.delete("name") is True
    assert store.get("name") is None


def test_delete_missing_key():
    store = Store(max_memory=3)

    assert store.delete("missing") is False


def test_exists():
    store = Store(max_memory=3)

    store.set("name", "Vinay")

    assert store.exists("name") is True
    assert store.exists("missing") is False


def test_ttl_expiration():
    store = Store(max_memory=3)

    store.set("temp", "hello", ttl=1)

    assert store.get("temp") == "hello"

    time.sleep(1.1)

    assert store.get("temp") is None


def test_lru_eviction():
    store = Store(max_memory=3)

    store.set("a", "1")
    store.set("b", "2")
    store.set("c", "3")

    # Make "a" recently used.
    assert store.get("a") == "1"

    # "b" should now be the least recently used.
    store.set("d", "4")

    assert store.get("a") == "1"
    assert store.get("b") is None
    assert store.get("c") == "3"
    assert store.get("d") == "4"