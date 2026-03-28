import asyncio
import logging
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass

from app.command import response
from app.command.const import ParsedCommand
from app.command.info import get_info
from app.parser import parser as resp_parser

logger = logger = logging.getLogger(__name__)

REPLICA_STREAMS: set["Replica"] = set()


@dataclass
class Replica:
    """
    Class containing data about the replicas
    """

    writer: StreamWriter
    reader: StreamReader

    async def send(self, thing: bytes) -> None:
        """
        Send data to the replicas
        """

        self.writer.write(thing)
        await self.writer.drain()

    async def poll_offset(self) -> int | None:
        """
        Tries to get the current offset from the replica
        """

        get_ack_cmd = resp_parser.encode_list(["REPLCONF", "GETACK", "*"])
        await self.send(get_ack_cmd)

        value = await resp_parser.parse_stream(self.reader)

        if not value:
            return None

        _, _, offset = value

        return int(offset)


async def num_replicas(requested: int, timeout: int) -> int:
    """
    Returns the amount of replicas that are up to date, up to the timeout or the requested amount
    """

    if not REPLICA_STREAMS:
        return 0

    if get_info().master_repl_offset == 0:
        return len(REPLICA_STREAMS)

    tasks = [asyncio.create_task(_poll_replica(replica)) for replica in REPLICA_STREAMS]
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
    REPLICA_STREAMS.add(Replica(writer, reader))


def send_replication(command: ParsedCommand) -> None:
    """
    Replicates commands to slaves
    """

    asyncio.create_task(_replicate(command))


async def _replicate(command: ParsedCommand) -> None:

    for i, replica in enumerate(REPLICA_STREAMS):
        logger.info(f"Replicating to slave {i}")

        await replica.send(command.original_command)


async def receive_replication(
    master_reader: StreamReader, master_writer: StreamWriter
) -> None:
    """
    Replicates data from a master without responding
    """

    logger.info("Awaiting data from master")

    while True:
        args = await resp_parser.parse_stream(master_reader)

        if args is None:
            break

        logger.info(f"Received {args}")

        cmd = await response.parse_command(args)
        get_info().increment_offset(len(cmd.original_command))

        if cmd.replication_response:
            master_writer.write(cmd.encode())
            await master_writer.drain()


async def _poll_replica(replica: Replica) -> None:

    while True:
        offset = await replica.poll_offset()

        if offset is None:
            continue

        logger.info(f"Received {offset}")

        if int(offset) >= get_info().master_repl_offset:
            return

        await asyncio.sleep(0.05)
