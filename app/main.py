import argparse
import logging
import sys
import asyncio

from app.command import info
from app.command.info import ReplicationRole
from app.response import async_parse

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_PORT = 6379


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

    is_master = args.replicaof is ReplicationRole.MASTER

    info.set_or_get_info(role=ReplicationRole.MASTER if is_master else ReplicationRole.SLAVE)

    async with server:
        logger.info("Starting Server")
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Redis in Python", description="Toy Redis Implementation in Python"
    )

    parser.add_argument("-p", "--port", default=REDIS_PORT)
    parser.add_argument("--replicaof", default=ReplicationRole.MASTER)

    asyncio.run(run_server(parser.parse_args()))
