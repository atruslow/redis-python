import asyncio
import logging

from app.parser import parser as resp_parser

logger = logging.getLogger(__name__)


async def handshake(
    master_host: str, master_port: str, server_port: str
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
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
    await _consume_rdb(reader)

    logger.info("Completed handshake with master")

    return reader, writer


async def _consume_rdb(reader: asyncio.StreamReader) -> None:
    """Read and discard the RDB file sent by the master after FULLRESYNC."""
    length_line = await reader.readline()  # $<len>\r\n
    length = int(length_line[1:].strip())
    await reader.readexactly(length)
    logger.info(f"Consumed RDB file ({length} bytes)")


async def _send(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    args: list,
) -> None:
    writer.write(resp_parser.encode(args))
    await writer.drain()
    resp = await reader.readline()
    logger.info(f"Master response: {resp!r}")
