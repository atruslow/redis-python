from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional


CACHE: Dict[str, "CacheItem"] = {}


@dataclass
class CacheItem:
    value: str
    expiry: Optional[datetime] = None

    def set_expiry(self, exp: int) -> None:
        self.expiry = datetime.now(timezone.utc) + timedelta(milliseconds=exp)

    @property
    def is_expired(self) -> bool:

        if not self.expiry:
            return False

        return self.expiry < datetime.now(timezone.utc)


def get_key(key: str) -> Optional[str]:

    if key not in CACHE:
        return None

    if CACHE[key].is_expired:
        del CACHE[key]
        return None

    return CACHE[key].value
