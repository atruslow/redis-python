import asyncio
import logging

from app.parser import parser as resp_parser

logger = logging.getLogger(__name__)


async def handshake(master_host: str, master_port: str, server_port: str) -> None:
    """
    Completes a handshake with the master if we are a slave
    """

    logger.info(f"Connecting to master {master_host}:{master_port}")
    reader, writer = await asyncio.open_connection(master_host, master_port)

    writer.write(resp_parser.encode([b"PING"]))
    await writer.drain()

    writer.write(resp_parser.encode([b"REPLCONF", b"listening-port", server_port]))
    await writer.drain()

    writer.write(resp_parser.encode([b"REPLCONF", b"capa", b"psync2"]))
    await writer.drain()
    logger.info("Completed handshake with master")

    writer.close()
    await writer.wait_closed()
