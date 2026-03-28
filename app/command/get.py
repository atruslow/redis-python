"""
Module for handling the get command
"""


from app.cache import cache
from app.command.const import Command, ParsedCommand


async def handle_get(args: list[str]) -> ParsedCommand:

    (key,) = args
    value = _get_key(key)

    return ParsedCommand(command=Command.Get, args=args, response=value)


def _get_key(key: str) -> bytes | None:

    value = cache.get_key(key)

    return value.encode() if value else None
