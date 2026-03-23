from typing import List

from app.cache.cache import set_key
from app.command.const import Command, ParsedCommand


def handle_set(args: List[str]) -> ParsedCommand:

    key, *value = args
    set_value = value[0]
    exp_milisec = None

    if "ex" in [i.lower() for i in value]:
        exp_milisec = int(value[-1]) * 1000

    if "px" in [i.lower() for i in value]:
        exp_milisec = int(value[-1])

    set_key(key, set_value, exp=exp_milisec)

    return ParsedCommand(command=Command.Set, args=args, response="OK")
