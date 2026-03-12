"""
Module for handling the get command
"""

from typing import List

from app.cache import cache
from app.command.const import Command, ParsedCommand, SIMPLE_NIL


def handle_get(args: List[str]) -> ParsedCommand:

    (key,) = args
    value = _get_key(key)

    return ParsedCommand(command=Command.Get, args=args, response=value)


def _get_key(key: str) -> str:

    value = cache.get_key(key)

    return value or SIMPLE_NIL
