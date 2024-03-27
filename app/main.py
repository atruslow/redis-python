import socket
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_PORT = 6379

import asyncio

async def handle_client(reader, writer):
    request = None
    while request != 'quit':

        request = (await reader.read(1024)).decode('utf8')
        logger.info(f"Got Message: {request}")

        writer.write("+PONG\r\n".encode())

        try:
            await writer.drain()
        except ConnectionResetError:
            logger.exception('')
            break

    writer.close()

async def run_server():
    server = await asyncio.start_server(handle_client, 'localhost', REDIS_PORT)
    async with server:
        logger.info("Starting Server")
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(run_server())
