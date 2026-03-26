from asyncio import StreamReader, StreamWriter
import asyncio
from typing import List, Set

from app import response
from app.command.const import ParsedCommand
from app.parser import parser as resp_parser

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

    while True:
        args = await resp_parser.parse_stream(reader)

        if args is None:
            break

        logger.info(f"Received {args}")

        cmd = response.parse_command(args)

        if cmd.replication_response:
            writer.write(cmd.encode())
            await writer.drain()
