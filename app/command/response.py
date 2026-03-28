from app.command import get, info, psync, replconf, set, wait
from app.command.const import Command, ParsedCommand


async def parse_command(msg: list[str]) -> ParsedCommand:
    """Dispatch a pre-tokenized command list to the appropriate handler."""
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
