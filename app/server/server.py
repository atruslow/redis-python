import argparse
import asyncio
import logging
from asyncio import StreamReader, StreamWriter

from app.command.const import Command, ParsedCommand
from app.command.info import ReplicationRole, get_info, init_info
from app.command.response import parse_command
from app.parser import parser as resp_parser
from app.replica import handshake, replication

logger = logging.getLogger(__name__)


async def run_server(args: argparse.Namespace):
    """
    Handles running the server, and spinning up background tasks for replicas
    """

    server = await asyncio.start_server(handle_client, "localhost", args.port)
    background_tasks = set()

    is_master = args.replicaof is None

    init_info(role=ReplicationRole.MASTER if is_master else ReplicationRole.SLAVE)

    if not is_master:
        master_host, master_port = args.replicaof
        conn = await handshake.handshake(master_host, master_port, args.port)
        background_tasks.add(
            asyncio.create_task(
                replication.receive_replication(replication.Master(*conn))
            )
        )

    async with server:
        logger.info(f"Starting Server on port {args.port}")
        await server.serve_forever()


async def handle_client(reader: StreamReader, writer: StreamWriter) -> None:
    """
    Handles a single client connection
    """

    while True:
        args = await resp_parser.parse_stream(reader)

        if args is None or args[0] == "quit":
            break

        command = await parse_command(args)
        logger.info(f"Got Message: {command}")

        writer.write(command.encode())
        if command.raw_extra is not None:
            writer.write(command.raw_extra)

        became_replica = _handle_replication(command, writer, reader)

        try:
            await writer.drain()
        except ConnectionResetError:
            logger.exception("")
            break

        if became_replica:
            return

    writer.close()


def _handle_replication(
    command: ParsedCommand, writer: StreamWriter, reader: StreamReader
) -> bool:

    if get_info().is_slave:
        return False

    match command.command:
        case Command.Psync:
            replication.set_replica(writer, reader)
            return True

        case Command.Set:
            get_info().increment_offset(len(command.original_command))
            replication.send_replication(command)

    return False
