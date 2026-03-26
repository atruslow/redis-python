from dataclasses import dataclass
from enum import StrEnum, auto
from typing import List, Optional

from app.parser import parser
from app.parser.parser import RESPValue
from app.parser import parser as resp_parser


class Command(StrEnum):
    Ping = auto()
    Echo = auto()
    Set = auto()
    Get = auto()
    Info = auto()
    Replconf = auto()
    Psync = auto()

    @classmethod
    def get_command(cls, cmd: str) -> "Command":
        try:
            return cls(cmd.lower())
        except ValueError:
            raise RuntimeError(f"Unknown command: {cmd!r}")


@dataclass
class ParsedCommand:
    command: Command
    args: List[str]
    response: Optional[RESPValue]
    raw_extra: Optional[bytes] = None

    def encode(self) -> bytes:
        return resp_parser.encode(self.response)
    
    @property
    def original_command(self) -> bytes:

        return parser.encode([self.command.upper().encode(), *[a.encode() for a in self.args]])

