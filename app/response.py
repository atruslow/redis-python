import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class Command(Enum):
    Ping = 1
    Echo = 2

    @classmethod
    def get_command(cls, cmd: str) -> "Command":
        match cmd.lower():
            case "ping":
                return cls.Ping
            case "echo":
                return cls.Echo
            case _:
                raise RuntimeError("Bad Command")


@dataclass
class ParsedCommand:
    command: Command
    args: List[str]
    response: Optional[str]

    def encode(self):
        return encode(self.response)


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
            return ParsedCommand(command=Command.Ping, args=rest, response="PONG")
        case Command.Echo:
            return ParsedCommand(
                command=Command.Echo, args=rest, response=" ".join(rest)
            )
        case _:
            raise RuntimeError("Bad Command")


def encode(msg: str) -> str:
    return "\r\n".join([f"${len(msg)}", msg, ""])
