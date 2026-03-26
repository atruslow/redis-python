import asyncio
import logging
from typing import Tuple

from app.parser import parser as resp_parser

logger = logging.getLogger(__name__)


async def handshake(master_host: str, master_port: str, server_port: str) -> Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """
    Completes a handshake with the master if we are a slave
    """
    logger.info(f"Connecting to master {master_host}:{master_port}")
    reader, writer = await asyncio.open_connection(master_host, master_port)

    await _send(reader, writer, [b"PING"])
    await _send(
        reader, writer, [b"REPLCONF", b"listening-port", str(server_port).encode()]
    )
    await _send(reader, writer, [b"REPLCONF", b"capa", b"psync2"])
    await _send(reader, writer, [b"PSYNC", b"?", b"-1"])

    logger.info("Completed handshake with master")

    return reader, writer


async def _send(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    args: list,
) -> None:
    writer.write(resp_parser.encode(args))
    await writer.drain()
    resp = await reader.read(1024)
    logger.info(f"Master response: {resp!r}")
