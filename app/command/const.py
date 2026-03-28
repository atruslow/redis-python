from dataclasses import dataclass
from enum import StrEnum, auto

from app.parser import parser
from app.parser import parser as resp_parser
from app.parser.parser import RESPValue


class Command(StrEnum):
    Ping = auto()
    Echo = auto()
    Set = auto()
    Get = auto()
    Info = auto()
    Replconf = auto()
    Psync = auto()
    Wait = auto()

    @classmethod
    def get_command(cls, cmd: str) -> "Command":
        try:
            return cls(cmd.lower())
        except ValueError as e:
            raise RuntimeError(f"Unknown command: {cmd!r}") from e


@dataclass
class ParsedCommand:
    command: Command
    args: list[str]
    response: RESPValue | None
    raw_extra: bytes | None = None
    replication_response: bool = False

    def encode(self) -> bytes:
        return resp_parser.encode(self.response)

    @property
    def original_command(self) -> bytes:

        return parser.encode(
            [self.command.upper().encode(), *[a.encode() for a in self.args]]
        )
