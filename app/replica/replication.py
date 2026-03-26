from asyncio import StreamReader, StreamWriter
import asyncio
from typing import List, Set

from app import response
from app.command.const import ParsedCommand
from app.parser import parser

import logging

logger = logger = logging.getLogger(__name__)

REPLICA_STREAMS: Set[StreamWriter] = set()


def set_replica(writer: StreamWriter) -> None:
    """
    Appends to the list of replicas
    """
    REPLICA_STREAMS.add(writer)


def send_replication(command: ParsedCommand) -> None:
    """
    Replicates commands to slaves
    """

    asyncio.create_task(_replicate(command))


async def _replicate(command: ParsedCommand) -> None:

    for i, replica_writer in enumerate(REPLICA_STREAMS):
        logger.info(f"Replicating to slave {i}")

        replica_writer.write(command.original_command)
        await replica_writer.drain()


async def receive_replication(reader: StreamReader, writer: StreamWriter) -> None:
    """
    Replicates data from a master without responding
    """

    logger.info("Awaiting data from master")

    while resp := await reader.read(1024):
        logger.info("Read data from master")

        command = resp.decode("utf-8")
        value = parser.parse_list(command)

        logger.info(f"Received {value}")

        response.parse_command(value)
