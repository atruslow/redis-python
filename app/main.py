import logging
import sys
import asyncio

from app.response import async_parse

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_PORT = 6379


async def handle_client(reader, writer):
    request = None
    while request != "quit":
        request = (await reader.read(1024)).decode("utf8")

        command = await async_parse(request)
        logger.info(f"Got Message: {command}")

        writer.write(command.encode().encode())

        try:
            await writer.drain()
        except ConnectionResetError:
            logger.exception("")
            break

    writer.close()


async def run_server():
    server = await asyncio.start_server(handle_client, "localhost", REDIS_PORT)
    async with server:
        logger.info("Starting Server")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(run_server())
