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
    resp = await reader.read(1024)
    logger.info(f"Master PING resp: {resp.decode()}")

    writer.write(resp_parser.encode([b"REPLCONF", b"listening-port", str(server_port).encode()]))
    await writer.drain()
    resp = await reader.read(1024)
    logger.info(f"Master REPLCONF listening-port resp: {resp.decode()}")

    writer.write(resp_parser.encode([b"REPLCONF", b"capa", b"psync2"]))
    await writer.drain()
    resp = await reader.read(1024)
    logger.info(f"Master REPLCONF capa resp: {resp.decode()}")

    logger.info("Completed handshake with master")

    writer.close()
    await writer.wait_closed()
