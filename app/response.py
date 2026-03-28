from app.command import get, info, psync, replconf, set, wait
from app.command.const import Command, ParsedCommand
from app.parser import parser as resp_parser


async def parse(msg: str) -> ParsedCommand:
    """Parse a raw RESP string into a ParsedCommand."""
    tokens = resp_parser.parse_str(msg)
    if not isinstance(tokens, list):
        raise resp_parser.RESPParseError(f"Expected array, got {type(tokens).__name__}")
    args = [t.decode() if isinstance(t, bytes) else str(t) for t in tokens]
    return await parse_command(args)


async def parse_command(msg: list[str]) -> ParsedCommand:
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
            return await set.handle_set(rest)
        case Command.Get:
            return await get.handle_get(rest)
        case Command.Info:
            return await info.handle_info(rest)
        case Command.Replconf:
            return await replconf.handle_replconf(rest)
        case Command.Psync:
            return await psync.handle_psync(rest)
        case Command.Wait:
            return await wait.handle_wait(rest)
        case _:
            raise RuntimeError("Bad Command")
