import argparse
import logging
import sys
import asyncio
import re
from typing import Tuple

from app.command.const import Command, ParsedCommand
from app.command.info import ReplicationRole, init_info, get_info
from app.response import parse_command
from app.replica import handshake, replication
from app.parser import parser as resp_parser

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_PORT = 6379
HOST_PORT_RE = re.compile(r"^(?P<host>\S+)\s+(?P<port>\d+)$")


async def handle_client(reader, writer):
    while True:
        args = await resp_parser.parse_stream(reader)

        if args is None or args[0] == "quit":
            break

        command = parse_command(args)
        logger.info(f"Got Message: {command}")

        writer.write(command.encode())
        if command.raw_extra is not None:
            writer.write(command.raw_extra)

        _handle_replication(command, writer)

        try:
            await writer.drain()
        except ConnectionResetError:
            logger.exception("")
            break

    writer.close()


def _handle_replication(command: ParsedCommand, writer: asyncio.StreamWriter) -> None:

    if get_info().is_slave:
        return

    match command.command:
        case Command.Psync:
            replication.set_replica(writer)

        case Command.Set:
            replication.send_replication(command)


async def run_server(args: argparse.Namespace):
    server = await asyncio.start_server(handle_client, "localhost", args.port)
    background_tasks = set()

    is_master = args.replicaof is None

    init_info(role=ReplicationRole.MASTER if is_master else ReplicationRole.SLAVE)

    if not is_master:
        master_host, master_port = args.replicaof
        conn = await handshake.handshake(master_host, master_port, args.port)
        background_tasks.add(
            asyncio.create_task(replication.receive_replication(*conn))
        )

    async with server:
        logger.info(f"Starting Server on port {args.port}")
        await server.serve_forever()


def _parse_host_port(arg_value: str) -> Tuple[str, str]:
    if m := HOST_PORT_RE.match(arg_value):
        return m.group("host"), m.group("port")
    raise argparse.ArgumentTypeError(
        f"'{arg_value}' is an invalid value. Does not match pattern: {HOST_PORT_RE}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Redis in Python", description="Toy Redis Implementation in Python"
    )

    parser.add_argument("-p", "--port", default=REDIS_PORT)
    parser.add_argument("--replicaof", type=_parse_host_port)

    asyncio.run(run_server(parser.parse_args()))
