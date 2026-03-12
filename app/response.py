import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from app.command.const import Command, ParsedCommand
from app.command import get
from app.cache.cache import set_key


SIMPLE_OK = "+OK\r\n"
SIMPLE_PONG = "+PONG\r\n"
SIMPLE_NIL = "$-1\r\n"

SIMPLE_RESPONSES = {SIMPLE_OK, SIMPLE_PONG, SIMPLE_NIL}


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
            set_value = value[0]
            exp_milisec = None

            if "ex" in [i.lower() for i in value]:
                exp_milisec = int(value[-1]) * 1000

            if "px" in [i.lower() for i in value]:
                exp_milisec = int(value[-1])

            set_key(key, set_value, exp=exp_milisec)

            return ParsedCommand(command=Command.Set, args=rest, response=SIMPLE_OK)

            return ParsedCommand(command=Command.Set, args=rest, response=SIMPLE_OK)
        case Command.Get:
            return get.handle_get(rest)

        case _:
            raise RuntimeError("Bad Command")


def encode(msg: str) -> str:

    if msg in SIMPLE_RESPONSES:
        return msg

    return "\r\n".join([f"${len(msg)}", msg, ""])
