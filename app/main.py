import argparse
import logging
import sys
import asyncio
import re
from typing import Tuple

from app.command import info
from app.command.info import ReplicationRole
from app.response import async_parse

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_PORT = 6379
HOST_PORT_RE = re.compile(r"^(?P<host>\S+)\s+(?P<port>\d+)$")


async def handle_client(reader, writer):
    request = None
    while request != "quit":
        request = (await reader.read(1024)).decode("utf8")

        if not request:
            break

        command = await async_parse(request)
        logger.info(f"Got Message: {command}")

        writer.write(command.encode().encode())

        try:
            await writer.drain()
        except ConnectionResetError:
            logger.exception("")
            break

    writer.close()


async def run_server(args: argparse.Namespace):
    server = await asyncio.start_server(handle_client, "localhost", args.port)

    is_master = args.replicaof is None

    # breakpoint()

    info.set_or_get_info(role=ReplicationRole.MASTER if is_master else ReplicationRole.SLAVE)

    if not is_master:
        master_host, master_port = args.replicaof
        logger.info(f"Connecting to master {master_host}:{master_port}")
        reader, writer = await asyncio.open_connection(master_host, master_port)
        writer.write("*1\r\n$4\r\nPING\r\n".encode())
        await writer.drain()

    async with server:
        logger.info(f"Starting Server on port {args.port}")
        await server.serve_forever()


def _parse_host_port(arg_value: str) -> Tuple[str, str]:
    if m := HOST_PORT_RE.match(arg_value):
        return m.group("host"), m.group("port")
    raise argparse.ArgumentTypeError(f"'{arg_value}' is an invalid value. Does not match pattern: {HOST_PORT_RE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Redis in Python", description="Toy Redis Implementation in Python"
    )

    parser.add_argument("-p", "--port", default=REDIS_PORT)
    parser.add_argument("--replicaof", type=_parse_host_port)

    asyncio.run(run_server(parser.parse_args()))
