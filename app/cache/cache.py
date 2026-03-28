from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

CACHE: dict[str, "CacheItem"] = {}


@dataclass
class CacheItem:
    value: str
    expiry: datetime | None = None

    def set_expiry(self, exp: int) -> None:
        self.expiry = datetime.now(timezone.utc) + timedelta(milliseconds=exp)

    @property
    def is_expired(self) -> bool:

        if not self.expiry:
            return False

        return self.expiry < datetime.now(timezone.utc)


def get_key(key: str) -> str | None:

    if key not in CACHE:
        return None

    if CACHE[key].is_expired:
        del CACHE[key]
        return None

    return CACHE[key].value


def set_key(key: str, value: str, exp: int | None = None) -> str:
    cache_item = CacheItem(value=value)

    if exp:
        cache_item.set_expiry(exp)

    CACHE[key] = cache_item
    return CACHE[key].value
