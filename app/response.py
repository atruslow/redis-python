import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import List


class Command(Enum):
    Ping = 1
    Echo = 2


@dataclass
class ParsedCommand:
    command: Command
    args: List[str]


async def async_parse(msg: str) -> List[str]:
    return await asyncio.get_event_loop().run_in_executor(None, parse, msg)


def parse(msg: str) -> List[str]:
    """
    Parses a decoded message from Redis, and returns a list of items
    """
    parsed_list = msg.split("\r\n")

    parsed_list = [
        i for i in parsed_list if i and not (i.startswith("*") or i.startswith("$"))
    ]

    return parsed_list


def parse_command(msg: List[str]) -> ParsedCommand:
    cmd, *rest = msg

    match cmd.lower():
        case "ping":
            return ParsedCommand(command=Command.Ping, args=rest)
        case "echo":
            return ParsedCommand(command=Command.Echo, args=rest)
        case _:
            raise RuntimeError("Bad Command")
