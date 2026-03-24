from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from app.parser.parser import RESPValue
from app.parser import parser as resp_parser


class Command(Enum):
    Ping = 1
    Echo = 2
    Set = 3
    Get = 4
    Info = 5
    Replconf = 6
    Psync = 7

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
            case "info":
                return cls.Info
            case "replconf":
                return cls.Replconf
            case "psync":
                return cls.Psync
            case _:
                raise RuntimeError("Bad Command")


@dataclass
class ParsedCommand:
    command: Command
    args: List[str]
    response: Optional[RESPValue]

    def encode(self) -> bytes:
        return resp_parser.encode(self.response)
