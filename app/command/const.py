from dataclasses import dataclass
from enum import StrEnum, auto

from app.parser import parser as resp_parser
from app.parser.parser import RESPValue


class Command(StrEnum):
    """Supported Redis commands; values are auto-lowercased names."""

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
        """Look up a Command by name (case-insensitive); raises RuntimeError if unknown."""
        try:
            return cls(cmd.lower())
        except ValueError as e:
            raise RuntimeError(f"Unknown command: {cmd!r}") from e


@dataclass
class ParsedCommand:
    """Result of parsing a single Redis command, including its encoded response."""

    command: Command
    args: list[str]
    response: RESPValue | None
    raw_extra: bytes | None = None
    replication_response: bool = False

    def encode(self) -> bytes:
        """Encode the response as RESP bytes."""
        return resp_parser.encode(self.response)

    @property
    def original_command(self) -> bytes:
        """Re-encode the command and args as a RESP array of bulk strings."""
        return resp_parser.encode_list([self.command.upper(), *self.args])
