import logging
from typing import List

from app.command.const import Command, ParsedCommand

logger = logging.getLogger(__name__)


def handle_replconf(args: List[str]) -> ParsedCommand:
    option, *values = args
    logger.info(f"REPLCONF {option} {' '.join(values)}")
    return ParsedCommand(command=Command.Replconf, args=args, response="OK")
