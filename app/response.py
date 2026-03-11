import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta, timezone


CACHE: Dict[str, "CacheItem"] = {}
SIMPLE_OK = "+OK\r\n"
SIMPLE_PONG = "+PONG\r\n"
SIMPLE_NIL = "$-1\r\n"

SIMPLE_RESPONSES = {SIMPLE_OK, SIMPLE_PONG, SIMPLE_NIL}


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


class Command(Enum):
    Ping = 1
    Echo = 2
    Set = 3
    Get = 4

    @classmethod
    def get_command(cls, cmd: str) -> "Command":
        match cmd.lower():
            case "ping":
                return cls.Ping
            case "echo":
                return cls.Echo
            case "set":
                return cls.Set
            case "get":
                return cls.Get
            case _:
                raise RuntimeError("Bad Command")


@dataclass
class ParsedCommand:
    command: Command
    args: List[str]
    response: Optional[str]

    def encode(self) -> str:
        return encode(self.response or "")


async def async_parse(msg: str) -> ParsedCommand:
    return await asyncio.get_event_loop().run_in_executor(None, parse, msg)


def parse(msg: str) -> ParsedCommand:
    """
    Parses a decoded message from Redis, and returns a list of items
    """

    parsed_list = msg.split("\r\n")

    parsed_list = [
        i for i in parsed_list if i and not (i.startswith("*") or i.startswith("$"))
    ]

    return parse_command(parsed_list)


def parse_command(msg: List[str]) -> ParsedCommand:
    cmd, *rest = msg
    command = Command.get_command(cmd)

    match command:
        case Command.Ping:
            return ParsedCommand(command=Command.Ping, args=rest, response=SIMPLE_PONG)
        case Command.Echo:
            return ParsedCommand(
                command=Command.Echo, args=rest, response=" ".join(rest)
            )
        case Command.Set:
            key, *value = rest

            if "ex" in [i.lower() for i in value]:
                exp_milisec = int(value[-1]) * 1000
                set_value = value[0]

                _set_key(key, set_value, exp=exp_milisec)

            if "px" in [i.lower() for i in value]:
                exp_milisec = int(value[-1])
                set_value = value[0]

                _set_key(key, set_value, exp=int(exp_milisec))

            return ParsedCommand(command=Command.Set, args=rest, response=SIMPLE_OK)
        case Command.Get:
            (key,) = rest
            value = _get_key(key)

            print(key, value)

            return ParsedCommand(command=Command.Get, args=rest, response=value)
        case _:
            raise RuntimeError("Bad Command")


def _set_key(key: str, value: str, exp: Optional[int] = None) -> str:
    cache_item = CacheItem(value=value)

    if exp:
        cache_item.set_expiry(exp)

    CACHE[key] = cache_item
    return CACHE[key].value


def _get_key(key: str) -> str:

    if key not in CACHE:
        return SIMPLE_NIL

    if CACHE[key].is_expired:
        del CACHE[key]
        return SIMPLE_NIL

    return CACHE[key].value


def encode(msg: str) -> str:

    if msg in SIMPLE_RESPONSES:
        return msg

    return "\r\n".join([f"${len(msg)}", msg, ""])
