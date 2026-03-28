from app.cache.cache import set_key
from app.command.const import Command, ParsedCommand


async def handle_set(args: list[str]) -> ParsedCommand:
    """Handle a SET command, storing the key with an optional EX/PX expiry."""
    key, set_value, *options = args
    exp_milisec = _parse_expiry(options)
    set_key(key, set_value, exp=exp_milisec)
    return ParsedCommand(command=Command.Set, args=args, response="OK")


def _parse_expiry(options: list[str]) -> int | None:
    it = iter(options)
    for opt in it:
        match opt.lower():
            case "ex":
                return int(next(it)) * 1000
            case "px":
                return int(next(it))
    return None
