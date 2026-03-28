import asyncio
import logging
from asyncio import StreamReader, StreamWriter

from app import response
from app.command.const import ParsedCommand
from app.command.info import get_info
from app.parser import parser as resp_parser

logger = logger = logging.getLogger(__name__)

REPLICA_STREAMS: set[tuple[StreamWriter, StreamReader]] = set()


async def num_replicas(requested: int, timeout: int) -> int:
    """
    Returns the amount of replicas that are up to date, up to the timeout or the requested amount
    """

    if not REPLICA_STREAMS:
        return 0

    if get_info().master_repl_offset == 0:
        return len(REPLICA_STREAMS)

    tasks = [
        asyncio.create_task(_poll_replicas(writer, reader))
        for (writer, reader) in REPLICA_STREAMS
    ]
    completed = 0

    try:
        async with asyncio.timeout(timeout / 1000):
            for coro in asyncio.as_completed(tasks):
                await coro
                completed += 1

                if requested == completed:
                    break

    except TimeoutError:
        pass
    finally:
        for t in tasks:
            t.cancel()

    return completed


def set_replica(writer: StreamWriter, reader: StreamReader) -> None:
    """
    Appends to the list of replicas
    """
    REPLICA_STREAMS.add((writer, reader))


def send_replication(command: ParsedCommand) -> None:
    """
    Replicates commands to slaves
    """

    asyncio.create_task(_replicate(command))


async def _replicate(command: ParsedCommand) -> None:

    for i, (replica_writer, _) in enumerate(REPLICA_STREAMS):
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

        cmd = await response.parse_command(args)
        get_info().increment_offset(len(cmd.original_command))

        if cmd.replication_response:
            writer.write(cmd.encode())
            await writer.drain()


async def _poll_replicas(writer: StreamWriter, reader: StreamReader) -> None:

    while True:
        get_ack_cmd = resp_parser.encode_list(["REPLCONF", "GETACK", "*"])
        writer.write(get_ack_cmd)
        await writer.drain()

        value = await resp_parser.parse_stream(reader)

        if not value:
            continue

        _, _, offset = value

        logger.info(f"Received {offset}")

        if int(offset) >= get_info().master_repl_offset:
            return

        await asyncio.sleep(0.05)

