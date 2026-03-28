import time

import pytest

from app.cache import cache
from app.cache.cache import CACHE, CacheItem


@pytest.fixture(autouse=True)
def clear_cache():
    CACHE.clear()


def test_set_and_get():
    cache.set_key("foo", "bar")
    assert cache.get_key("foo") == "bar"


def test_get_missing_key():
    assert cache.get_key("nope") is None


def test_set_overwrites():
    cache.set_key("foo", "bar")
    cache.set_key("foo", "baz")
    assert cache.get_key("foo") == "baz"


def test_expiry_px():
    cache.set_key("foo", "bar", exp=50)
    assert cache.get_key("foo") == "bar"
    time.sleep(0.06)
    assert cache.get_key("foo") is None


def test_expiry_deletes_key():
    cache.set_key("foo", "bar", exp=50)
    time.sleep(0.06)
    cache.get_key("foo")
    assert "foo" not in CACHE


def test_no_expiry():
    cache.set_key("foo", "bar")
    item = CACHE["foo"]
    assert item.expiry is None
    assert not item.is_expired


def test_cache_item_is_expired_false_without_expiry():
    item = CacheItem(value="x")
    assert not item.is_expired
