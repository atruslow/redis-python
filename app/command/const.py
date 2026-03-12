from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

SIMPLE_OK = "+OK\r\n"
SIMPLE_PONG = "+PONG\r\n"
SIMPLE_NIL = "$-1\r\n"

SIMPLE_RESPONSES = {SIMPLE_OK, SIMPLE_PONG, SIMPLE_NIL}


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


def encode(msg: str) -> str:

    if msg in SIMPLE_RESPONSES:
        return msg

    return "\r\n".join([f"${len(msg)}", msg, ""])
