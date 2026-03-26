from asyncio import StreamWriter
import base64
import logging
from pathlib import Path
from typing import List

from app.command.const import Command, ParsedCommand
from app.command.info import get_info
from app.replica import replication

logger = logging.getLogger(__name__)

_RDB_PATH = Path(__file__).parent / "data" / "empty_rdb.txt"


def _load_rdb() -> bytes:
    rdb = base64.b64decode(_RDB_PATH.read_text().strip())
    return f"${len(rdb)}\r\n".encode() + rdb


async def handle_psync(args: List[str]) -> ParsedCommand:
    replication_id, offset = args
    logger.info(f"PSYNC replication_id={replication_id} offset={offset}")

    info = get_info()
    response = f"FULLRESYNC {info.master_replid} 0"

    return ParsedCommand(
        command=Command.Psync,
        args=args,
        response=response,
        raw_extra=_load_rdb(),
    )
