import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from app.command.const import Command, ParsedCommand
from app.command import get, set, const


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
            return ParsedCommand(
                command=Command.Ping, args=rest, response=const.SIMPLE_PONG
            )
        case Command.Echo:
            return ParsedCommand(
                command=Command.Echo, args=rest, response=" ".join(rest)
            )
        case Command.Set:
            return set.handle_set(rest)

        case Command.Get:
            return get.handle_get(rest)

        case _:
            raise RuntimeError("Bad Command")


def encode(msg: str) -> str:

    if msg in const.SIMPLE_RESPONSES:
        return msg

    return "\r\n".join([f"${len(msg)}", msg, ""])
