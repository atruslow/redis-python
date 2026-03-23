import asyncio
from typing import List

from app.command.const import Command, ParsedCommand
from app.command import get, info, set
from app.parser import parser as resp_parser


async def async_parse(msg: str) -> ParsedCommand:
    return await asyncio.get_event_loop().run_in_executor(None, parse, msg)


def parse(msg: str) -> ParsedCommand:
    """
    Parses a decoded message from Redis and returns a ParsedCommand.
    """
    tokens = resp_parser.parse_str(msg)
    if not isinstance(tokens, list):
        raise resp_parser.RESPParseError(f"Expected array, got {type(tokens).__name__}")
    args = [t.decode() if isinstance(t, bytes) else str(t) for t in tokens]
    return parse_command(args)


def parse_command(msg: List[str]) -> ParsedCommand:
    cmd, *rest = msg
    command = Command.get_command(cmd)

    match command:
        case Command.Ping:
            return ParsedCommand(command=Command.Ping, args=rest, response="PONG")
        case Command.Echo:
            return ParsedCommand(
                command=Command.Echo, args=rest, response=" ".join(rest).encode()
            )
        case Command.Set:
            return set.handle_set(rest)
        case Command.Get:
            return get.handle_get(rest)
        case Command.Info:
            return info.handle_info(rest)
        case _:
            raise RuntimeError("Bad Command")
