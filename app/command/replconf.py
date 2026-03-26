import logging
from typing import List

from app.command.const import Command, ParsedCommand
from app.command.info import get_info

logger = logging.getLogger(__name__)


async def handle_replconf(args: List[str]) -> ParsedCommand:
    option, *values = args
    logger.info(f"REPLCONF {option} {' '.join(values)}")

    info = get_info()

    if option == "GETACK" and info.is_slave:
        response = [b"REPLCONF", b"ACK", str(info.master_repl_offset).encode("utf8")]
        return ParsedCommand(
            command=Command.Replconf,
            args=args,
            response=response,
            replication_response=True,
        )

    return ParsedCommand(command=Command.Replconf, args=args, response="OK")
