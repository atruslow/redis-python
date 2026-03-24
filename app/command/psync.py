import logging
from typing import List

from app.command.const import Command, ParsedCommand
from app.command.info import get_info

logger = logging.getLogger(__name__)


def handle_psync(args: List[str]) -> ParsedCommand:
    replication_id, offset = args
    logger.info(f"PSYNC replication_id={replication_id} offset={offset}")

    info = get_info()
    response = f"FULLRESYNC {info.master_replid} 0"

    return ParsedCommand(command=Command.Psync, args=args, response=response)
